"""Live mode end to end (no network, model mocked) + 'my hospital isn't listed'.

Link or PDF -> fetch -> text -> grounded reader -> sanity checks -> rules in memory -> eligibility -> packet.
Every failure has a code; nothing is written to disk.
"""

import io
import json
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient
from pypdf import PdfReader, PdfWriter

from backend import app as app_module
from backend import live_session, policies
from backend.policy_reader import extract_text, fetch
from backend.policy_reader.cache import DEFAULT_CACHE_DIR
from backend.policy_reader.llm_clients import ModelResult
from backend.tests.pdf_factory import make_pdf

client = TestClient(app_module.app)
FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "sample_rules.json").read_text())
_QUOTES = [FIXTURE[f]["evidence"]["quote"] for f in ("free_care", "discount", "asset_test", "residency", "application_window")]
POLICY_PAGE = (
    "Unseen Valley Hospital Financial Assistance Policy. Charity care applies to uninsured and underinsured patients.\n"
    + "\n".join(q for q in _QUOTES if q) + "\n"
) * 3


class FakeModel:
    def __init__(self):
        self.calls = 0

    def generate(self, prompt):
        self.calls += 1
        data = {**FIXTURE, "hospital_name": "Unseen Valley Hospital", "hospital_state": "OH"}
        return ModelResult(text=json.dumps(data), input_tokens=1000, output_tokens=200, seconds=0.0, model="fake")


@pytest.fixture(autouse=True)
def _fresh(monkeypatch):
    live_session.clear()
    model = FakeModel()
    monkeypatch.setattr("backend.policy_reader.reader.default_client", lambda: model)
    monkeypatch.setenv("LIVE_MODE", "1")
    monkeypatch.setenv("DEMO_CACHE_ONLY", "0")
    yield model
    live_session.clear()


def _cache_files() -> set[str]:
    return {p.name for p in Path(DEFAULT_CACHE_DIR).rglob("*") if p.is_file()}


def _upload(pdf: bytes):
    return client.post("/api/policy/read", files={"file": ("policy.pdf", pdf, "application/pdf")})


# ---------- happy path on a hospital that is not in the curated set ----------

def test_unseen_hospital_full_flow_in_memory_only(_fresh):
    before = _cache_files()
    resp = _upload(make_pdf([POLICY_PAGE, POLICY_PAGE]))
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["slug"].startswith("live-") and data["source"] == "live"
    assert data["grounded"]["free_care"]["value"] == 200
    assert data["grounded"]["free_care"]["verified"] is True and data["grounded"]["free_care"]["source_quote"]
    slug = data["slug"]

    elig = client.post("/api/eligibility", json={"hospital_slug": slug, "household_size": 2,
                                                 "annual_income": 30000, "state": "OH"}).json()["data"]
    assert elig["status"] == "likely_free" and elig["hospital_name"] == "Unseen Valley Hospital"

    packet = client.post("/api/packet", json={
        "bill": {"hospital_name": "Unseen Valley Hospital"}, "hospital_slug": slug, "household_size": 2,
        "annual_income": 30000, "eligibility": {"status": "likely_free", "percent_of_fpl": elig["percent_of_fpl"],
                                                 "quote": elig["evidence"]["quote"], "page": elig["evidence"]["page"]},
        "lang": "es"})
    assert packet.status_code == 200 and packet.content.startswith(b"%PDF")
    assert client.get(f"/api/policy/facts?slug={slug}").json()["data"]["has_page_images"] is False
    assert _cache_files() == before, "live mode must not write anything to disk"


def test_quote_missing_from_the_pdf_needs_checking_and_is_never_a_pass(_fresh):
    """The model 'quotes' rules the PDF doesn't contain: code marks them unverified and the engine won't say free."""
    page = "Unseen Valley Hospital Financial Assistance Policy. Charity care for uninsured patients.\n" + _QUOTES[0] + "\n"
    data = _upload(make_pdf([page * 6])).json()["data"]
    assert data["grounded"]["residency"]["verified"] is False
    assert "quote_not_found" in data["grounded"]["residency"]["problems"]
    assert "residency" in data["needs_checking"]
    elig = client.post("/api/eligibility", json={"hospital_slug": data["slug"], "household_size": 2,
                                                 "annual_income": 30000, "state": "OH"}).json()["data"]
    assert elig["status"] == "cannot_determine"


def test_same_pdf_twice_reuses_the_session_copy_not_disk(_fresh):
    pdf = make_pdf([POLICY_PAGE])
    a, b = _upload(pdf).json()["data"], _upload(pdf).json()["data"]
    assert a["slug"] == b["slug"]


def test_curated_link_is_served_from_cache_without_download_or_model(_fresh, monkeypatch):
    def no_fetch(url):
        raise AssertionError("must not download a curated policy")

    monkeypatch.setattr(app_module, "fetch_policy", no_fetch)
    url = next(h["source_url"] for h in policies.load_index() if h["slug"] == "fort-healthcare-inc")
    data = client.post("/api/policy/read", json={"url": url}).json()["data"]
    assert data["slug"] == "fort-healthcare-inc" and data["source"] == "curated"
    assert _fresh.calls == 0


def test_session_entries_expire_and_have_a_size_cap(monkeypatch):
    now = [0.0]
    monkeypatch.setattr(live_session, "_clock", lambda: now[0])
    rules = policies.load_policy("fort-healthcare-inc")[0]
    live_session.put("live-aaaa", rules)
    now[0] += live_session.TTL_SECONDS + 1
    assert live_session.get("live-aaaa") is None
    monkeypatch.setattr(live_session, "MAX_ENTRIES", 2)
    for i in range(3):
        live_session.put(f"live-{i}", rules)
    assert live_session.size() == 2 and live_session.get("live-0") is None


def test_expired_live_slug_says_read_it_again():
    resp = client.post("/api/eligibility", json={"hospital_slug": "live-deadbeef", "household_size": 2,
                                                 "annual_income": 1, "state": "OH"})
    assert resp.status_code == 404 and resp.json()["code"] == "not_found"


# ---------- every live-mode failure has a code ----------

def _encrypted_pdf() -> bytes:
    writer = PdfWriter()
    writer.append(PdfReader(io.BytesIO(make_pdf([POLICY_PAGE]))))
    writer.encrypt("secret")
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


@pytest.mark.parametrize("pdf,code", [
    (_encrypted_pdf(), "pdf_encrypted"),
    (b"%PDF-1.4 this is not really a pdf", "pdf_empty"),
    (make_pdf(["", ""]), "pdf_empty"),
    (make_pdf(["Financial assistance policy. Charity care is available; see the poverty table at the desk."]), "too_short"),
    (make_pdf(["Cafeteria menu for the week. Soup, salad and sandwiches are served daily from noon. " * 15]), "not_policy"),
])
def test_unreadable_documents_get_a_clear_code(pdf, code, _fresh):
    resp = _upload(pdf)
    assert resp.status_code == 422, resp.text
    assert resp.json()["code"] == code
    assert _fresh.calls == 0, "no model call for a document we can't use"


def test_link_turned_off_says_so(monkeypatch):
    monkeypatch.setenv("LIVE_MODE", "0")
    resp = client.post("/api/policy/read", json={"url": "https://example.org/fap.pdf"})
    assert resp.status_code == 403 and resp.json()["code"] == "live_off"


@pytest.mark.parametrize("error,code", [
    (fetch.FetchError("the website returned HTTP 404", "fetch_failed"), "fetch_failed"),
    (fetch.FetchError("the website took too long to answer", "fetch_timeout"), "fetch_timeout"),
    (fetch.FetchError("that link is not a PDF or a web page", "not_pdf"), "not_pdf"),
    (fetch.FetchError("no financial assistance policy found on that page", "no_pdf_link"), "no_pdf_link"),
    (fetch.FetchError("URL must start with http:// or https://", "bad_url"), "bad_url"),
])
def test_fetch_failures_map_to_codes(error, code, monkeypatch):
    def failing(url):
        raise error

    monkeypatch.setattr(app_module, "fetch_policy", failing)
    resp = client.post("/api/policy/read", json={"url": "https://unseen.example.org/fap"})
    assert resp.json()["code"] == code and resp.json()["success"] is False


def _fake_web(monkeypatch, routes: dict):
    """Serve `routes` {url: (content_type, body)} through httpx without the network."""
    def handler(request: httpx.Request) -> httpx.Response:
        if str(request.url) not in routes:
            raise httpx.ConnectTimeout("timed out", request=request)
        ctype, body = routes[str(request.url)]
        return httpx.Response(200, headers={"content-type": ctype}, content=body)

    real_client = httpx.Client
    monkeypatch.setattr(fetch.httpx, "Client", lambda **kw: real_client(transport=httpx.MockTransport(handler), **kw))
    monkeypatch.setattr(fetch, "_assert_public_host", lambda url: None)


def test_html_page_with_a_policy_pdf_link(monkeypatch):
    pdf = make_pdf([POLICY_PAGE])
    _fake_web(monkeypatch, {
        "https://h.example.org/billing": ("text/html", b'<a href="/docs/Financial-Assistance-Policy.pdf">FAP</a>'),
        "https://h.example.org/docs/Financial-Assistance-Policy.pdf": ("application/pdf", pdf),
    })
    got = fetch.fetch_policy("https://h.example.org/billing")
    assert got.kind == "pdf" and got.pdf_bytes == pdf


def test_html_page_that_is_the_policy_is_read_as_text(monkeypatch):
    html = "<html><body><script>var x=1;</script><h1>Financial Assistance</h1><p>" + POLICY_PAGE + "</p></body></html>"
    _fake_web(monkeypatch, {"https://h.example.org/fap": ("text/html; charset=utf-8", html.encode())})
    got = fetch.fetch_policy("https://h.example.org/fap")
    assert got.kind == "html_text" and "var x" not in got.text and "200%" in got.text


def test_html_page_without_a_policy(monkeypatch):
    _fake_web(monkeypatch, {"https://h.example.org/": ("text/html", b"<p>Welcome to our hospital</p>")})
    with pytest.raises(fetch.FetchError) as err:
        fetch.fetch_policy("https://h.example.org/")
    assert err.value.code == "no_pdf_link"


def test_download_timeout(monkeypatch):
    _fake_web(monkeypatch, {})
    with pytest.raises(fetch.FetchError) as err:
        fetch.fetch_policy("https://slow.example.org/fap.pdf")
    assert err.value.code == "fetch_timeout"


def test_html_policy_through_the_api(monkeypatch, _fresh):
    monkeypatch.setattr(app_module, "fetch_policy",
                        lambda url: fetch.FetchedPolicy("html_text", url, text=POLICY_PAGE))
    data = client.post("/api/policy/read", json={"url": "https://unseen.example.org/fap"}).json()["data"]
    assert data["slug"].startswith("live-") and "web page" in " ".join(data["rules"]["warnings"])


def test_document_checks_directly():
    for text, code in [("", "pdf_empty"), ("Financial assistance: see the desk.", "too_short")]:
        with pytest.raises(extract_text.DocumentError) as err:
            extract_text.doc_from_text(text)
        assert err.value.code == code


# ---------- enter the limits by hand ----------

def test_manual_limits_flow():
    data = client.post("/api/policy/manual", json={"hospital_name": "Unseen Valley Hospital", "state": "oh",
                                                   "free_max_percent": 250, "discount_max_percent": 400}).json()["data"]
    assert data["slug"].startswith("live-manual-") and data["source"] == "manual"
    elig = client.post("/api/eligibility", json={"hospital_slug": data["slug"], "household_size": 1,
                                                 "annual_income": 35000, "state": "OH"}).json()["data"]
    assert elig["status"] == "likely_free"  # 35,000 / 15,960 = 219% <= 250%


@pytest.mark.parametrize("body", [
    {"free_max_percent": 300, "discount_max_percent": 250},  # discount below free
    {"free_max_percent": 700},  # outside 100-600
    {"free_max_percent": 50},
])
def test_manual_limits_are_checked(body):
    resp = client.post("/api/policy/manual", json={"hospital_name": "X Hospital", "state": "OH", **body})
    assert resp.status_code == 422 and resp.json()["code"] == "invalid_input"


# ---------- my hospital isn't listed ----------

def test_search_finds_by_name_typo_city_and_state():
    assert policies.search_hospitals("marshfeld")[0]["slug"] == "marshfield-clinic-health-system"
    assert policies.search_hospitals("Mobile")[0]["slug"] == "usa-health"
    assert {r["slug"] for r in policies.search_hospitals("WI")} >= {"fort-healthcare-inc", "marshfield-clinic-health-system"}


def test_search_does_not_match_a_different_hospital_on_a_shared_word():
    assert policies.search_hospitals("Mayo Clinic") == []
    assert client.get("/api/hospitals/search?q=St%20Jude%20Childrens").json()["data"] == []


def test_unknown_hospital_is_not_matched():
    data = client.post("/api/hospitals/match", json={"hospital_name": "Mayo Clinic Rochester",
                                                     "hospital_address": "200 First St SW, Rochester, MN 55905"}).json()["data"]
    assert data["matched"] is False and data["reason"]
