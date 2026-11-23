import json
from pathlib import Path

import pytest

from backend.eob_reader import reader
from backend.eob_reader.schema import CONFIRM_THRESHOLD, eob_strict_schema
from backend.policy_reader.llm_clients import ModelResult, PolicyReaderError

BILL_PDF = Path(__file__).parent / "fixtures" / "bills" / "bill_a_text.pdf"
BILL_IMAGE = Path(__file__).parent / "fixtures" / "bills" / "bill_b_photo.png"


def field(value, confidence=0.95, location="page 1, claim table", note=""):
    return {"value": value, "confidence": confidence, "location": location, "note": note}


def payload(**claim_overrides):
    claim = {
        "service_date": field("03/14/2026"),
        "provider": field("SAMPLE GENERAL HOSPITAL (FICTIONAL)"),
        "billed_amount": field("$1,234.56"),
        "allowed_amount": field("$900.00"),
        "plan_paid": field("$700.00"),
        "patient_responsibility": field("$200.00"),
        "deductible": field("$100.00"),
        "copay": field("$25.00"),
        "coinsurance": field("$75.00"),
        "status": "paid",
        "status_confidence": 0.96,
        "status_location": "page 1, status",
        "remark_codes": [],
    }
    claim.update(claim_overrides)
    return json.dumps({"plan_name": field("Sample Health Plan"), "claims": [claim]})


class FakeClient:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.prompts = []

    def generate(self, prompt):
        self.prompts.append(prompt)
        text = self.responses.pop(0)
        return ModelResult(text=text, input_tokens=100, output_tokens=50, seconds=0.01, model="fake")


def test_schema_excludes_patient_and_member_identifiers():
    text = json.dumps(eob_strict_schema()).lower()
    for banned in ("patient_name", "member_id", "date_of_birth", "diagnosis"):
        assert banned not in text


def test_reader_normalizes_money_and_dates():
    result = reader.read_eob(BILL_IMAGE.read_bytes(), "image/png", client=FakeClient(payload()))
    claim = result.document.claims[0]
    assert claim.service_date.normalized == "2026-03-14"
    assert claim.billed_amount.normalized == 123456
    assert claim.patient_responsibility.normalized == 20000
    assert result.fields_to_confirm == []


def test_low_confidence_or_missing_location_requires_confirmation():
    result = reader.read_eob(
        BILL_PDF.read_bytes(),
        "application/pdf",
        client=FakeClient(payload(patient_responsibility=field("$200.00", 0.7, ""))),
    )
    assert "claims.0.patient_responsibility" in result.fields_to_confirm
    assert result.document.claims[0].patient_responsibility.confidence < CONFIRM_THRESHOLD


def test_invalid_schema_retries_once_then_succeeds():
    client = FakeClient("not json", payload())
    result = reader.read_eob(BILL_PDF.read_bytes(), "application/pdf", client=client)
    assert result.model == "fake"
    assert len(client.prompts) == 2 and client.prompts[1].correction


def test_invalid_schema_twice_fails_cleanly_without_values():
    with pytest.raises(PolicyReaderError, match="invalid after retry"):
        reader.read_eob(BILL_PDF.read_bytes(), "application/pdf", client=FakeClient("bad", "also bad"))


def test_wrong_file_type_is_rejected():
    with pytest.raises(reader.EobReadError):
        reader.read_eob(b"hello", "text/plain", client=FakeClient(payload()))
