"""BillBack API. Requests are processed in memory; uploads are never written to disk."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any, Literal, Optional

from fastapi import FastAPI, HTTPException, Request, Response, UploadFile
from fastapi.responses import JSONResponse
from starlette.formparsers import MultiPartParser
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

import hashlib

from backend import demo_mode, errors, fpl, hospital_form, packet, policies
from backend.errors import AppError
from backend.llm_retry import ModelUnavailable
from backend.policy_reader import cache as policy_cache
from backend.bill_reader import reader as bill_reader
from backend.eligibility import eligibility_result_to_api_response, load_fpl_table_from_json, run_eligibility
from backend import live_session, manual_policy, rate_limit
from backend.policy_reader import grounding
from backend.policy_reader.extract_text import DocumentError
from backend.policy_reader.fetch import MAX_BYTES, FetchError, fetch_policy
from backend.policy_reader.reader import PolicyReaderError, read_policy, read_policy_text

log = logging.getLogger("billback")
# Uploads stay in memory: Starlette spools multipart parts over 1 MB to a temp file on disk by default.
MultiPartParser.spool_max_size = MAX_BYTES + 1024 * 1024
MAX_REQUEST_BYTES = MAX_BYTES + 1024 * 1024  # 25 MB file + form overhead; checked before the body is parsed

app = FastAPI(title="BillBack API")
errors.install(app)


@app.middleware("http")
async def _cap_request_size(request: Request, call_next):
    length = request.headers.get("content-length")
    if length and length.isdigit() and int(length) > MAX_REQUEST_BYTES:
        return JSONResponse(errors.error_body("too_large", "file is larger than 25 MB"), status_code=413)
    return await call_next(request)
MAX_HOUSEHOLD = 20  # API and UI agree: 1-20 people


def _envelope(data: Any = None, error: str | None = None) -> dict[str, Any]:
    return {"success": error is None, "data": data, "error": error}


@app.get("/api/health")
def health() -> dict[str, Any]:
    return _envelope({"ok": True})


@dataclass(frozen=True)
class _PolicyInput:
    pdf_bytes: bytes = b""
    text: str = ""
    url: Optional[str] = None
    curated_slug: Optional[str] = None  # a link to a policy we already read: no download, no model call


async def _policy_input(request: Request) -> _PolicyInput:
    ctype = request.headers.get("content-type", "")
    if ctype.startswith("multipart/form-data"):
        form = await request.form()
        upload = form.get("file")
        if upload is None or not hasattr(upload, "read"):
            raise AppError("bad_file", "send the PDF as form field 'file'")
        data = await upload.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise AppError("too_large", "file is larger than 25 MB")
        if not data.startswith(b"%PDF"):
            raise AppError("bad_file", "file is not a PDF")
        return _PolicyInput(pdf_bytes=data)
    if ctype.startswith("application/json"):
        if not demo_mode.live_mode():
            raise AppError("live_off", "reading a policy from a link is turned off (LIVE_MODE=0)")
        try:
            body = await request.json()
        except ValueError as exc:
            raise AppError("bad_url", "send {\"url\": \"https://...\"}") from exc
        url = body.get("url") if isinstance(body, dict) else None
        if not isinstance(url, str) or not url.strip() or len(url) > 2048:
            raise AppError("bad_url", "paste a link that starts with https://")
        curated = policies.curated_slug_for_url(url)
        if curated:
            return _PolicyInput(url=url.strip(), curated_slug=curated)
        try:
            got = await run_in_threadpool(fetch_policy, url)
        except FetchError as exc:
            raise AppError(exc.code, str(exc)) from exc
        return _PolicyInput(pdf_bytes=got.pdf_bytes, text=got.text, url=got.url)
    raise HTTPException(415, "send multipart/form-data with 'file', or JSON with 'url'")


def _policy_payload(rules: Any, slug: str, *, source: str, cached: bool, seconds: float, beta: bool) -> dict[str, Any]:
    return {
        "slug": slug,
        "source": source,  # "curated" (read and checked earlier) | "live" (read just now, memory only) | "manual"
        "hospital_name": rules.hospital_name,
        "state": rules.hospital_state,
        "rules": rules.model_dump(mode="json"),
        "grounded": grounding.grounded_view(rules),
        "needs_checking": grounding.needs_checking(rules),
        "cached": cached,
        "seconds": round(seconds, 2),
        "timings": {"policy_read_s": round(seconds, 2)},
        "beta": beta,
    }


def _curated(slug: str, seconds: float, beta: bool) -> dict[str, Any]:
    rules, _ = policies.load_policy(slug)
    return _policy_payload(rules, slug, source="curated", cached=True, seconds=seconds, beta=beta)


def _curated_slug_for_sha(sha: str) -> Optional[str]:
    hit = policy_cache.lookup(sha)
    if hit is None:
        return None
    for h in policies.load_index():
        if hit.source and h["file"].endswith(f"__{hit.source.sha256[:8]}.json"):
            return h["slug"]
    return None


@app.post("/api/policy/read")
async def policy_read(request: Request) -> dict[str, Any]:
    """Live mode: a policy link or PDF -> grounded rules, kept in memory for this session only (never on disk).
    A policy we already read and checked is served from the curated cache instead."""
    started = time.perf_counter()
    rate_limit.check(request, "policy_read")
    got = await _policy_input(request)
    beta = got.url is not None
    sha = policy_cache.sha256_bytes(got.pdf_bytes) if got.pdf_bytes else None
    curated = got.curated_slug or (_curated_slug_for_sha(sha) if sha else None) or policies.curated_slug_for_url(got.url)
    if curated:
        return _envelope(_curated(curated, time.perf_counter() - started, beta))
    if demo_mode.demo_cache_only():
        raise AppError("demo_only", "demo mode: this policy isn't cached, so it can't be read right now")
    try:
        if got.pdf_bytes:
            result = await run_in_threadpool(lambda: read_policy(got.pdf_bytes, url=got.url, persist=False))
        else:
            result = await run_in_threadpool(lambda: read_policy_text(got.text, url=got.url))
    except DocumentError as exc:
        raise AppError(exc.code, str(exc)) from exc
    except ModelUnavailable as exc:
        log.warning("policy reader: model unavailable after retries: %s", exc)
        raise AppError("ai_unavailable", "the policy reader is busy right now; try again or enter the limits by hand") from exc
    except PolicyReaderError as exc:
        log.exception("policy reader failed")
        raise AppError("ai_invalid", "could not read that policy; try the PDF or enter the limits by hand") from exc
    key = (sha or policy_cache.sha256_bytes(got.text.encode("utf-8")))[: live_session.SLUG_HEX]
    slug = live_session.put(f"{live_session.PREFIX}{key}", result.rules)
    return _envelope(_policy_payload(result.rules, slug, source="live", cached=False, seconds=result.seconds, beta=beta))


class ManualPolicyRequest(BaseModel):
    hospital_name: str = Field(..., min_length=2, max_length=200)
    state: str = Field(..., min_length=2, max_length=2, pattern="^[A-Za-z]{2}$")
    free_max_percent: float = Field(..., ge=100, le=600, description="Free care up to this % of the poverty line")
    discount_max_percent: Optional[float] = Field(None, ge=100, le=600, description="Some discount up to this %")


@app.post("/api/policy/manual")
def policy_manual(req: ManualPolicyRequest, request: Request) -> dict[str, Any]:
    """The patient types the limits from the hospital's policy (when the link or PDF can't be read). Memory only."""
    rate_limit.check(request, "policy_manual")
    if req.discount_max_percent is not None and req.discount_max_percent < req.free_max_percent:
        raise AppError("invalid_input", "the discount limit can't be lower than the free-care limit",
                       extra={"fields": ["discount_max_percent"]})
    rules = manual_policy.build(req.hospital_name, req.state, req.free_max_percent, req.discount_max_percent)
    slug = live_session.put(manual_policy.slug_for(rules), rules)
    return _envelope(_policy_payload(rules, slug, source="manual", cached=False, seconds=0.0, beta=False))


@app.post("/api/bill/read")
async def bill_read(file: UploadFile) -> dict[str, Any]:
    """Multipart 'file' (photo or PDF). Read into memory only; never saved."""
    data = await file.read(bill_reader.MAX_BILL_BYTES + 1)
    if demo_mode.bill_cache_only():
        hit = demo_mode.cached_bill(hashlib.sha256(data).hexdigest())
        if hit is None:
            raise AppError("demo_only", "demo mode: only the sample bills can be read right now")
        return _envelope({**hit, "cached": True})
    if len(data) > bill_reader.MAX_BILL_BYTES:
        raise AppError("too_large", "file is larger than 15 MB")
    try:
        result = await run_in_threadpool(bill_reader.read_bill, data, file.content_type or "")
    except bill_reader.BillReadError as exc:
        raise AppError("bad_file", str(exc)) from exc
    except ModelUnavailable as exc:
        log.warning("bill reader: model unavailable after retries: %s", exc)
        raise AppError("ai_unavailable", "the bill reader is busy right now; type the details in instead") from exc
    except PolicyReaderError as exc:
        log.exception("bill reader failed")
        raise AppError("ai_invalid", "could not read that bill; please try again") from exc
    return _envelope(result.to_dict())


class EligibilityRequest(BaseModel):
    hospital_slug: str = Field(..., max_length=60)
    household_size: int = Field(..., ge=1, le=MAX_HOUSEHOLD)
    annual_income: float = Field(..., ge=0, le=10_000_000)
    state: str = Field(..., min_length=2, max_length=2, description="Household's state (picks the FPL row)")
    assets_usd: float | None = Field(None, ge=0, description="Total household assets (optional)")
    insurance_status: str | None = Field(None, max_length=20, description="uninsured / insured / underinsured (optional)")
    residency_state: str | None = Field(None, min_length=2, max_length=2, description="State of residency if different (optional)")


_fpl_resolver_cache: dict[str, Any] = {}


def _fpl_resolver(table: dict[str, Any]):
    key = f"{table['year']}:{table.get('source_url')}"
    if key not in _fpl_resolver_cache:
        _fpl_resolver_cache.clear()
        _fpl_resolver_cache[key] = load_fpl_table_from_json(table)
    return _fpl_resolver_cache[key]


@app.post("/api/eligibility")
def eligibility(req: EligibilityRequest) -> dict[str, Any]:
    """B's rules engine (plain code, no AI) on a cached policy, with the 2026 HHS poverty guidelines."""
    started = time.perf_counter()
    try:
        rules, _ = policies.load_policy(req.hospital_slug)
        table = fpl._default_table()
        pct = fpl.percent_of_fpl(req.annual_income, req.household_size, req.state, table=table)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    except FileNotFoundError as exc:
        log.error("FPL table missing: %s", exc)
        raise HTTPException(503, "poverty guideline table is not loaded yet") from exc

    result = run_eligibility(
        rules=rules,
        household_size=req.household_size,
        annual_income=req.annual_income,
        state=req.state,
        fpl_resolver=_fpl_resolver(table),
        fpl_year=int(table["year"]),
        assets_usd=req.assets_usd,
        insurance_status=req.insurance_status,
        residency_state=req.residency_state,
    )
    data = eligibility_result_to_api_response(result, rules, pct, policies.source_url_for(rules))
    return _envelope({**data, "timings": {"rules_s": round(time.perf_counter() - started, 4)}})


class PacketBill(BaseModel):
    hospital_name: str = Field("", max_length=300)
    hospital_address: str = Field("", max_length=500)
    amount_due: str = Field("", max_length=40)
    service_date: str = Field("", max_length=40)
    account_number: str = Field("", max_length=60)


class PacketEligibility(BaseModel):
    status: str = Field(..., max_length=40)
    percent_of_fpl: float = Field(..., ge=0, le=100_000)
    quote: str = Field("", max_length=2000)
    page: int | None = Field(None, ge=0, le=10_000)
    fpl_year: int | None = Field(None, ge=2000, le=2100)


class PacketRequest(BaseModel):
    bill: PacketBill
    hospital_slug: str = Field(..., max_length=60)
    household_size: int = Field(..., ge=1, le=MAX_HOUSEHOLD)
    annual_income: float = Field(..., ge=0, le=10_000_000)
    eligibility: PacketEligibility
    lang: Literal["en", "es"] = "en"
    kind: Literal["application", "appeal"] = "application"
    benefits: bool = False  # optional SNAP/Medicaid/WIC answer: adds the benefit letter to the checklist


@app.post("/api/packet")
def packet_pdf(req: PacketRequest) -> Response:
    """Request letter + checklist as a PDF, built in memory and streamed back. Never saved."""
    started = time.perf_counter()
    try:
        rules, _ = policies.load_policy(req.hospital_slug)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    if req.kind == "appeal":
        pdf = packet.build_appeal(
            bill=req.bill.model_dump(),
            hospital_name=req.bill.hospital_name or rules.hospital_name,
            household_size=req.household_size,
            annual_income=req.annual_income,
            percent_of_fpl=req.eligibility.percent_of_fpl,
            fpl_year=req.eligibility.fpl_year or 2026,
            quote=req.eligibility.quote,
            page=req.eligibility.page or None,
            source_url=policies.source_url_for(rules),
            lang=req.lang,
        )
        return Response(
            content=pdf,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="BillBack-appeal-{req.hospital_slug}.pdf"',
                "Cache-Control": "no-store",
            },
        )
    own_form = hospital_form.form_for(req.hospital_slug, req.lang)
    pdf = packet.build_packet(
        bill=req.bill.model_dump(),
        hospital_name=req.bill.hospital_name or rules.hospital_name,
        household_size=req.household_size,
        annual_income=req.annual_income,
        percent_of_fpl=req.eligibility.percent_of_fpl,
        fpl_year=req.eligibility.fpl_year or 2026,
        quote=req.eligibility.quote,
        page=req.eligibility.page or None,
        source_url=policies.source_url_for(rules),
        how_to_apply=rules.how_to_apply,
        lang=req.lang,
        benefits=req.benefits,
        own_form_hospital=own_form.hospital if own_form else None,
    )
    if own_form is not None:
        pdf = hospital_form.append_form(pdf, own_form)
    filename = f"BillBack-application-{req.hospital_slug}.pdf"
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"', "Cache-Control": "no-store",
                 "X-Packet-Seconds": f"{time.perf_counter() - started:.3f}"},
    )


@app.get("/api/config")
def config() -> dict[str, Any]:
    """What the UI may offer. live_mode=False hides "paste a link to the policy"."""
    return _envelope({"live_mode": demo_mode.live_mode()})


@app.get("/api/hospitals")
def hospitals() -> dict[str, Any]:
    """Every hospital with a cached policy: [{slug, name, state}]."""
    return _envelope(policies.list_hospitals())


class MatchRequest(BaseModel):
    hospital_name: str | None = Field(None, max_length=300)
    hospital_address: str | None = Field(None, max_length=500)


@app.get("/api/hospitals/search")
def hospitals_search(q: str = "") -> dict[str, Any]:
    """Fuzzy search over curated hospitals (name, other names, city, state). [] -> show "My hospital isn't listed"."""
    if len(q) > 100:
        raise AppError("invalid_input", "search is too long")
    return _envelope(policies.search_hospitals(q))


@app.post("/api/hospitals/match")
def hospitals_match(req: MatchRequest) -> dict[str, Any]:
    """Best cached policy for a bill's hospital. matched=false (score < 80) -> UI asks the patient to pick."""
    return _envelope(policies.match_hospital(req.hospital_name, req.hospital_address))


# --- Result-screen extras: public policy facts only, plain code, no AI (backend/policy_page.py, policy_facts.py) ---
from backend import policy_facts, policy_page  # noqa: E402


def _policy_lookup(fn, *args):
    try:
        return fn(*args)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc


@app.get("/api/policy/page")
def policy_page_image(slug: str, page: int, quote: str = "") -> dict[str, Any]:
    """One policy page as a PNG + a box per line of the quote. found=false -> no box is drawn."""
    if len(quote) > policy_page.MAX_QUOTE_CHARS:
        raise HTTPException(400, "quote is too long")
    return _envelope(_policy_lookup(policy_page.locate, slug, page, quote))


@app.get("/api/policy/thresholds")
def policy_thresholds(slug: str, household_size: int, state: str) -> dict[str, Any]:
    if not 1 <= household_size <= MAX_HOUSEHOLD:
        raise AppError("invalid_input", f"household_size must be 1-{MAX_HOUSEHOLD}")
    return _envelope(_policy_lookup(policy_facts.thresholds, slug, household_size, state))


@app.get("/api/policy/facts")
def policy_facts_route(slug: str) -> dict[str, Any]:
    return _envelope(_policy_lookup(policy_facts.facts, slug))
