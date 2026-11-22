import hashlib
import json
from pathlib import Path

from fastapi.testclient import TestClient

from backend import app as app_module
from backend import demo_mode

client = TestClient(app_module.app)
POLICY = Path(__file__).resolve().parents[2] / "data" / "policies" / "usa-health-al.pdf"


def test_demo_cache_only_serves_cached_policy_without_model(monkeypatch):
    monkeypatch.setenv("DEMO_CACHE_ONLY", "1")
    monkeypatch.setattr(app_module, "read_policy", lambda *a, **k: (_ for _ in ()).throw(AssertionError("model called")))
    resp = client.post("/api/policy/read", files={"file": ("p.pdf", POLICY.read_bytes(), "application/pdf")})
    assert resp.status_code == 200 and resp.json()["data"]["cached"] is True


def test_demo_cache_only_refuses_uncached_policy(monkeypatch):
    monkeypatch.setenv("DEMO_CACHE_ONLY", "1")
    resp = client.post("/api/policy/read", files={"file": ("p.pdf", b"%PDF-1.4 new policy", "application/pdf")})
    assert resp.status_code == 409


def test_live_mode_off_blocks_url_reads(monkeypatch):
    monkeypatch.setenv("LIVE_MODE", "0")
    resp = client.post("/api/policy/read", json={"url": "https://example.org/fap.pdf"})
    assert resp.status_code == 403


def test_bill_cache_only_serves_cached_bill(monkeypatch, tmp_path):
    data = b"%PDF-1.4 fake sample bill bytes"
    sha = hashlib.sha256(data).hexdigest()
    (tmp_path / f"{sha}.json").write_text(json.dumps({"fields": {}, "fields_to_confirm": [], "seconds": 1.0, "model": "cached"}))
    monkeypatch.setattr(demo_mode, "BILL_CACHE_DIR", tmp_path)
    monkeypatch.setenv("BILL_CACHE_ONLY", "1")
    resp = client.post("/api/bill/read", files={"file": ("b.pdf", data, "application/pdf")})
    assert resp.status_code == 200 and resp.json()["data"]["cached"] is True
    resp = client.post("/api/bill/read", files={"file": ("x.pdf", b"%PDF other", "application/pdf")})
    assert resp.status_code == 409
