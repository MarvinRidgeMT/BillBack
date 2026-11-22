import io
import json
import os
from datetime import date, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from backend import app as app_module
from backend.bill_reader import image_prep, reader, validate
from backend.bill_reader.schema import FIELD_NAMES, bill_strict_schema
from backend.policy_reader.llm_clients import ModelResult

BILLS = Path(__file__).parent / "fixtures" / "bills"


def model_json(**overrides) -> str:
    fields = {
        "hospital_name": {"value": "SAMPLE GENERAL HOSPITAL (FICTIONAL)", "confidence": 0.95, "note": ""},
        "hospital_address": {"value": "100 Example Way, Springfield, OH 45501", "confidence": 0.9, "note": ""},
        "amount_due": {"value": "$1,234.56", "confidence": 0.95, "note": ""},
        "service_date": {"value": "03/14/2026", "confidence": 0.9, "note": ""},
        "account_number": {"value": "ZZ-TEST-0001", "confidence": 0.9, "note": ""},
    }
    fields.update(overrides)
    return json.dumps(fields)


class FakeClient:
    def __init__(self, payload: str):
        self.payload = payload
        self.prompts = []

    def generate(self, prompt):
        self.prompts.append(prompt)
        return ModelResult(text=self.payload, input_tokens=1500, output_tokens=150, seconds=0.01, model="fake-model")


# ---------- schema / privacy ----------

def test_schema_has_only_the_five_bill_fields_and_no_patient_data():
    schema = bill_strict_schema()
    assert set(schema["properties"]) == set(FIELD_NAMES)
    text = json.dumps(schema).lower()
    for banned in ("patient_name", "date_of_birth", "dob", "insurance"):
        assert banned not in text


def test_patient_fields_from_model_are_dropped():
    extra = json.loads(model_json())
    extra["patient_name"] = {"value": "Testy McTestface", "confidence": 1, "note": ""}
    result = reader.read_bill((BILLS / "bill_a_text.pdf").read_bytes(), "application/pdf", client=FakeClient(json.dumps(extra)))
    dumped = json.dumps(result.to_dict())
    assert "Testy" not in dumped and "patient_name" not in dumped


# ---------- validation ----------

def test_amount_parses_to_cents():
    assert validate.parse_cents("$1,234.56") == 123456
    assert validate.parse_cents("12750") == 1275000
    assert validate.parse_cents("abc") is None
    assert validate.parse_cents("-$5.00") is None


def test_service_date_parses_to_iso_and_rejects_future():
    assert validate.parse_service_date("03/14/2026") == "2026-03-14"
    assert validate.parse_service_date("2026-02-02") == "2026-02-02"
    assert validate.parse_service_date("Jan 9, 2026") == "2026-01-09"
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    assert validate.parse_service_date(tomorrow) is None
    assert validate.parse_service_date("not a date") is None


@pytest.mark.parametrize("value,ok", [("ZZ-TEST-0001", True), ("FAKE998877", True), ("12", False), ("AB 12 34", False), ("A" * 31, False), ("ab$12", False)])
def test_account_number_rule(value, ok):
    assert validate.valid_account_number(value) is ok


def test_failed_check_caps_confidence_and_lists_field():
    payload = model_json(amount_due={"value": "call us", "confidence": 0.95, "note": ""})
    result = reader.read_bill((BILLS / "bill_a_text.pdf").read_bytes(), "application/pdf", client=FakeClient(payload))
    assert result.fields["amount_due"].confidence <= 0.5
    assert "amount_due" in result.fields_to_confirm


def test_text_pdf_value_not_in_text_is_capped():
    payload = model_json(account_number={"value": "ZZ-TEST-9999", "confidence": 0.95, "note": ""})
    result = reader.read_bill((BILLS / "bill_a_text.pdf").read_bytes(), "application/pdf", client=FakeClient(payload))
    assert result.fields["account_number"].confidence <= 0.5
    assert "not found" in result.fields["account_number"].note


def test_clean_text_pdf_needs_no_confirmation_and_normalizes():
    result = reader.read_bill((BILLS / "bill_a_text.pdf").read_bytes(), "application/pdf", client=FakeClient(model_json()))
    assert result.fields_to_confirm == []
    assert result.fields["amount_due"].normalized == 123456
    assert result.fields["service_date"].normalized == "2026-03-14"
    assert result.model == "fake-model"


def test_low_model_confidence_goes_to_confirm():
    payload = model_json(hospital_address={"value": "100 Example Way", "confidence": 0.6, "note": "blurry"})
    result = reader.read_bill((BILLS / "bill_a_text.pdf").read_bytes(), "application/pdf", client=FakeClient(payload))
    assert "hospital_address" in result.fields_to_confirm


def test_missing_value_goes_to_confirm():
    payload = model_json(account_number={"value": "", "confidence": 0.1, "note": "not on bill"})
    result = reader.read_bill((BILLS / "bill_a_text.pdf").read_bytes(), "application/pdf", client=FakeClient(payload))
    assert result.fields["account_number"].value is None
    assert "account_number" in result.fields_to_confirm


# ---------- images ----------

def test_image_resized_to_1600_and_sent_as_jpeg():
    big = Image.new("RGB", (4000, 3000), "white")
    buf = io.BytesIO()
    big.save(buf, format="PNG")
    part = image_prep.prepare_image(buf.getvalue())
    out = Image.open(io.BytesIO(part.data))
    assert max(out.size) == 1600 and part.media_type == "image/jpeg"


def test_rotated_low_contrast_png_goes_to_model_as_image():
    client = FakeClient(model_json(hospital_name={"value": "DEMO VALLEY HOSPITAL (NOT REAL)", "confidence": 0.7, "note": ""}))
    result = reader.read_bill((BILLS / "bill_c_rotated_lowcontrast.png").read_bytes(), "image/png", client=client)
    sent = client.prompts[0]
    assert len(sent.images) == 1 and sent.pdf_bytes is None
    assert "hospital_name" in result.fields_to_confirm


def test_rejects_unsupported_and_corrupt_files():
    with pytest.raises(reader.BillReadError):
        reader.read_bill(b"hello", "text/plain", client=FakeClient(model_json()))
    with pytest.raises(reader.BillReadError):
        reader.read_bill(b"not really a png", "image/png", client=FakeClient(model_json()))


# ---------- API ----------

client = TestClient(app_module.app)


def test_api_bill_read_returns_fields(monkeypatch):
    monkeypatch.setattr(reader, "default_client", lambda: FakeClient(model_json()))
    pdf = (BILLS / "bill_a_text.pdf").read_bytes()
    resp = client.post("/api/bill/read", files={"file": ("bill.pdf", pdf, "application/pdf")})
    body = resp.json()
    assert resp.status_code == 200, body
    data = body["data"]
    assert set(data) >= {"fields", "fields_to_confirm", "seconds", "model"}
    assert data["fields"]["amount_due"]["normalized"] == 123456


def test_api_bill_read_rejects_wrong_type():
    resp = client.post("/api/bill/read", files={"file": ("x.txt", b"hello", "text/plain")})
    assert resp.status_code == 400


@pytest.mark.live
@pytest.mark.skipif(not (os.getenv("ANTHROPIC_API_KEY") or os.getenv("GEMINI_API_KEY")), reason="no model API key in env")
def test_live_fake_bill():
    result = reader.read_bill((BILLS / "bill_b_photo.png").read_bytes(), "image/png")
    assert result.fields["amount_due"].normalized == 38910
