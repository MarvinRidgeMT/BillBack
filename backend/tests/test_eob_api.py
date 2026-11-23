from types import SimpleNamespace

from fastapi.testclient import TestClient

from backend import app as app_module
from backend.tests.test_eob_reader import payload

client = TestClient(app_module.app)


def test_eob_read_endpoint(monkeypatch):
    result = SimpleNamespace(to_dict=lambda: {"document": {"plan_name": {}, "claims": []}, "fields_to_confirm": []})
    monkeypatch.setattr(app_module.eob_reader, "read_eob", lambda data, content_type: result)
    response = client.post("/api/eob/read", files={"file": ("eob.png", b"image bytes", "image/png")})
    assert response.status_code == 200
    assert response.json()["success"] is True


def test_eob_compare_endpoint_is_deterministic():
    import json

    eob = json.loads(payload())
    for field in eob["claims"][0].values():
        if isinstance(field, dict) and "value" in field:
            value = field["value"].replace("$", "").replace(",", "")
            if value.replace(".", "", 1).isdigit():
                field["normalized"] = round(float(value) * 100)
    eob["claims"][0]["service_date"]["normalized"] = "2026-03-14"
    response = client.post(
        "/api/eob/compare",
        json={
            "bill": {
                "provider": "SAMPLE GENERAL HOSPITAL (FICTIONAL)",
                "service_date": "2026-03-14",
                "amount_due_cents": 30000,
            },
            "eob": eob,
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["match_score"] >= 75
    assert any(item["code"] == "more_than_patient_responsibility" for item in data["discrepancies"])


def test_insurance_letter_endpoint_returns_private_pdf():
    response = client.post(
        "/api/eob/letter",
        json={
            "kind": "billing_hold",
            "lang": "en",
            "hospital": "Sample Hospital",
            "account_number": "ABC-123",
            "service_date": "2026-03-14",
            "bill_amount": "$300.00",
            "eob_patient_responsibility": "$200.00",
            "claim_status": "pending",
        },
    )
    assert response.status_code == 200
    assert response.content.startswith(b"%PDF")
    assert response.headers["cache-control"] == "no-store"


def test_insurance_letter_rejects_unknown_language():
    response = client.post("/api/eob/letter", json={"kind": "billing_hold", "lang": "fr"})
    assert response.status_code == 422
