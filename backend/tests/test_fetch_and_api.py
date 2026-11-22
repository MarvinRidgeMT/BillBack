import pytest
from fastapi.testclient import TestClient

from backend import app as app_module
from backend.policy_reader import fetch
from backend.policy_reader.reader import ReadResult
from backend.policy_reader.schema import PolicyRules
from backend.tests.test_policy_reader import FIXTURE


@pytest.mark.parametrize("url", ["http://127.0.0.1/x.pdf", "http://localhost/x.pdf", "http://169.254.169.254/latest", "file:///etc/passwd", "ftp://example.org/a.pdf"])
def test_fetch_blocks_private_and_non_http(url):
    with pytest.raises(fetch.FetchError):
        fetch.fetch_policy_pdf(url)


def test_finds_fap_pdf_link_on_html_page():
    html = '<a href="/docs/menu.pdf">menu</a> <a href="/docs/Financial-Assistance-Policy.pdf">FAP</a>'
    assert fetch._find_policy_pdf_link(html, "https://hosp.example.org/billing/") == "https://hosp.example.org/docs/Financial-Assistance-Policy.pdf"


client = TestClient(app_module.app)


def test_api_rejects_non_pdf_upload():
    resp = client.post("/api/policy/read", files={"file": ("x.pdf", b"hello", "application/pdf")})
    assert resp.status_code == 400


def test_api_rejects_bad_content_type():
    resp = client.post("/api/policy/read", content=b"x", headers={"content-type": "text/plain"})
    assert resp.status_code == 415


def test_api_upload_returns_rules_envelope(monkeypatch):
    rules = PolicyRules.model_validate_json(FIXTURE.read_text())
    monkeypatch.setattr(app_module, "read_policy", lambda pdf, url=None: ReadResult(rules=rules, cached=True, seconds=0.0))
    resp = client.post("/api/policy/read", files={"file": ("p.pdf", b"%PDF-1.4 fake", "application/pdf")})
    body = resp.json()
    assert resp.status_code == 200 and body["success"] is True
    assert body["data"]["rules"]["free_care"]["fpl_max_percent"] == 200
