"""BillBack API. Requests are processed in memory; uploads are never written to disk."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, HTTPException, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from backend import fpl, policies
from backend.bill_reader import reader as bill_reader
from backend.eligibility import eligibility_result_to_api_response, load_fpl_table_from_json, run_eligibility
from backend.policy_reader.fetch import MAX_BYTES, FetchError, fetch_policy_pdf
from backend.policy_reader.reader import PolicyReaderError, read_policy

log = logging.getLogger("billback")
app = FastAPI(title="BillBack API")


def _envelope(data: Any = None, error: str | None = None) -> dict[str, Any]:
    return {"success": error is None, "data": data, "error": error}


@app.get("/api/health")
def health() -> dict[str, Any]:
    return _envelope({"ok": True})


async def _pdf_from_request(request: Request) -> tuple[bytes, str | None]:
    ctype = request.headers.get("content-type", "")
    if ctype.startswith("multipart/form-data"):
        form = await request.form()
        upload = form.get("file")
        if upload is None or not hasattr(upload, "read"):
            raise HTTPException(400, "send the PDF as form field 'file'")
        data = await upload.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise HTTPException(413, "file is larger than 25 MB")
        if not data.startswith(b"%PDF"):
            raise HTTPException(400, "file is not a PDF")
        return data, None
    if ctype.startswith("application/json"):
        body = await request.json()
        url = body.get("url") if isinstance(body, dict) else None
        if not isinstance(url, str) or len(url) > 2048:
            raise HTTPException(400, "send {\"url\": \"https://...\"}")
        try:
            return await run_in_threadpool(fetch_policy_pdf, url)
        except FetchError as exc:
            raise HTTPException(400, str(exc)) from exc
    raise HTTPException(415, "send multipart/form-data with 'file', or JSON with 'url'")


@app.post("/api/policy/read")
async def policy_read(request: Request) -> dict[str, Any]:
    pdf_bytes, url = await _pdf_from_request(request)
    try:
        result = await run_in_threadpool(read_policy, pdf_bytes, url=url)
    except PolicyReaderError as exc:
        log.exception("policy reader failed")
        raise HTTPException(502, "could not read that policy; please try again") from exc
    return _envelope(
        {
            "rules": result.rules.model_dump(mode="json"),
            "cached": result.cached,
            "seconds": round(result.seconds, 2),
        }
    )


@app.post("/api/bill/read")
async def bill_read(file: UploadFile) -> dict[str, Any]:
    """Multipart 'file' (photo or PDF). Read into memory only; never saved."""
    data = await file.read(bill_reader.MAX_BILL_BYTES + 1)
    try:
        result = await run_in_threadpool(bill_reader.read_bill, data, file.content_type or "")
    except bill_reader.BillReadError as exc:
        raise HTTPException(400, str(exc)) from exc
    except PolicyReaderError as exc:
        log.exception("bill reader failed")
        raise HTTPException(502, "could not read that bill; please try again") from exc
    return _envelope(result.to_dict())


class EligibilityRequest(BaseModel):
    hospital_slug: str = Field(..., max_length=60)
    household_size: int = Field(..., ge=1, le=30)
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
    return _envelope(eligibility_result_to_api_response(result, rules, pct, policies.source_url_for(rules)))


@app.get("/api/hospitals")
def hospitals() -> dict[str, Any]:
    """Every hospital with a cached policy: [{slug, name, state}]."""
    return _envelope(policies.list_hospitals())


class MatchRequest(BaseModel):
    hospital_name: str | None = Field(None, max_length=300)
    hospital_address: str | None = Field(None, max_length=500)


@app.post("/api/hospitals/match")
def hospitals_match(req: MatchRequest) -> dict[str, Any]:
    """Best cached policy for a bill's hospital. matched=false (score < 80) -> UI asks the patient to pick."""
    return _envelope(policies.match_hospital(req.hospital_name, req.hospital_address))
