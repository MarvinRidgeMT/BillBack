"""Failure handling: each failure is detected, reported with a stable code, and keeps what was already read.

1. Unreadable/blurry photo (blurred copy of a sample bill, made with Pillow here)
2. Model API error / timeout / rate limit (mocked client): backoff, 3 tries, time budget, clean 503
3. Low-confidence fields go to the patient to confirm
4. Invalid household input
(Hospital not found: backend/tests/test_live_mode.py)
"""

import io
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image, ImageFilter

from backend import llm_retry
from backend.app import app
from backend.bill_reader import quality
from backend.bill_reader import reader as bill_reader
from backend.policy_reader.llm_clients import ModelResult, PolicyReaderError, PromptInput, TransientModelError

REPO = Path(__file__).resolve().parents[2]
SHARP = REPO / "sample_bills" / "bill_01_clean.jpg"
client = TestClient(app)


@pytest.fixture(scope="module")
def blurry_jpeg() -> bytes:
    img = Image.open(SHARP).convert("RGB").filter(ImageFilter.GaussianBlur(4))
    out = io.BytesIO()
    img.save(out, format="JPEG", quality=85)
    return out.getvalue()


def fields_json(conf: float, blank: tuple[str, ...] = ()) -> str:
    values = {"hospital_name": "USA Health", "hospital_address": "1200 Magnolia Grove Blvd, Mobile, AL 36617",
              "amount_due": "$4,812.00", "service_date": "08/14/2026", "account_number": "UH-4471902"}
    return json.dumps({k: {"value": "" if k in blank else v, "confidence": conf, "note": ""} for k, v in values.items()})


class FakeClient:
    """Returns queued outcomes in order: a JSON string, or an exception to raise."""

    def __init__(self, *outcomes):
        self.outcomes, self.calls = list(outcomes), 0

    def generate(self, prompt: PromptInput) -> ModelResult:
        self.calls += 1
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return ModelResult(text=outcome, input_tokens=100, output_tokens=50, seconds=0.0, model="fake")


# ---------- 1. blurry / unreadable photo ----------

def test_sharp_sample_bill_passes_quality_check():
    q = quality.check_image(SHARP.read_bytes())
    assert q.ok and q.checked and q.sharpness > quality.SHARPNESS_MIN


def test_blurred_copy_is_detected_as_blurry(blurry_jpeg):
    q = quality.check_image(blurry_jpeg)
    assert not q.ok and quality.REASON_BLURRY in q.reasons


def test_tiny_photo_is_too_small():
    out = io.BytesIO()
    Image.open(SHARP).convert("RGB").resize((300, 390)).save(out, format="JPEG")
    assert quality.REASON_TOO_SMALL in quality.check_image(out.getvalue()).reasons


def test_blurry_photo_with_shaky_fields_is_unreadable_but_keeps_what_was_read(blurry_jpeg):
    fake = FakeClient(fields_json(0.45, blank=("account_number",)))
    res = bill_reader.read_bill(blurry_jpeg, "image/jpeg", client=fake)
    body = res.to_dict()
    assert body["unreadable"] is True
    assert body["quality"]["reasons"] == ["blurry"]
    # Everything that was read is still returned, so the manual form can be pre-filled.
    assert body["fields"]["hospital_name"]["value"] == "USA Health"
    assert "account_number" in body["weak_fields"]


def test_blurry_photo_read_confidently_is_only_a_warning(blurry_jpeg):
    res = bill_reader.read_bill(blurry_jpeg, "image/jpeg", client=FakeClient(fields_json(0.95)))
    assert res.unreadable is False and res.quality.ok is False


def test_sharp_photo_missing_three_fields_is_unreadable():
    fake = FakeClient(fields_json(0.9, blank=("amount_due", "service_date", "account_number")))
    assert bill_reader.read_bill(SHARP.read_bytes(), "image/jpeg", client=fake).unreadable is True


# ---------- 2. model API error / timeout / rate limit ----------

def test_transient_errors_retry_with_exponential_backoff_then_succeed():
    sleeps = []
    fake = FakeClient(TransientModelError("429"), TransientModelError("timeout"), fields_json(0.9))
    llm_retry.generate_with_retry(fake, PromptInput("x", ""), sleep=sleeps.append)
    assert fake.calls == 3 and sleeps == [1.0, 2.0]


def test_three_failures_raise_model_unavailable():
    fake = FakeClient(*[TransientModelError("503")] * 3)
    with pytest.raises(llm_retry.ModelUnavailable):
        llm_retry.generate_with_retry(fake, PromptInput("x", ""), sleep=lambda s: None)
    assert fake.calls == 3


def test_total_time_budget_stops_retries():
    now = [0.0]
    fake = FakeClient(*[TransientModelError("timeout")] * 3)

    def slow_sleep(seconds):
        now[0] += 28.0  # a try plus backoff used up almost the whole 30 s budget

    with pytest.raises(llm_retry.ModelUnavailable):
        llm_retry.generate_with_retry(fake, PromptInput("x", ""), sleep=slow_sleep, clock=lambda: now[0],
                                      total_timeout_s=30.0)
    assert fake.calls == 1


def test_non_transient_error_is_not_retried():
    fake = FakeClient(PolicyReaderError("bad API key"), fields_json(0.9))
    with pytest.raises(PolicyReaderError):
        llm_retry.generate_with_retry(fake, PromptInput("x", ""), sleep=lambda s: None)
    assert fake.calls == 1


def test_api_returns_clean_503_with_code_and_no_stack_trace(monkeypatch):
    monkeypatch.setattr(bill_reader, "default_client", lambda: FakeClient(*[TransientModelError("429")] * 3))
    monkeypatch.setattr(llm_retry.time, "sleep", lambda s: None)
    resp = client.post("/api/bill/read", files={"file": ("bill.jpg", SHARP.read_bytes(), "image/jpeg")})
    assert resp.status_code == 503
    body = resp.json()
    assert body["code"] == "ai_unavailable" and body["success"] is False
    assert "Traceback" not in resp.text and "TransientModelError" not in resp.text


def test_curated_hospital_eligibility_never_calls_the_model(monkeypatch):
    """Curated hospitals use cached rules, so an AI outage can't block the result."""
    def boom():
        raise AssertionError("model must not be called")

    monkeypatch.setattr(bill_reader, "default_client", boom)
    resp = client.post("/api/eligibility", json={"hospital_slug": "fort-healthcare-inc", "household_size": 2,
                                                 "annual_income": 20000, "state": "WI"})
    assert resp.status_code == 200 and resp.json()["data"]["status"] == "likely_free"


# ---------- 3. low-confidence fields ----------

def test_fields_under_point_eight_must_be_confirmed():
    res = bill_reader.read_bill(SHARP.read_bytes(), "image/jpeg", client=FakeClient(fields_json(0.79)))
    assert set(res.fields_to_confirm) == set(res.fields)


# ---------- 5. invalid household input ----------

@pytest.mark.parametrize("body,field", [
    ({"household_size": 0, "annual_income": 20000}, "household_size"),
    ({"household_size": 21, "annual_income": 20000}, "household_size"),
    ({"household_size": 3, "annual_income": -5}, "annual_income"),
    ({"household_size": 3}, "annual_income"),
])
def test_invalid_household_input_is_rejected_with_the_field_named(body, field):
    resp = client.post("/api/eligibility", json={"hospital_slug": "fort-healthcare-inc", "state": "WI", **body})
    assert resp.status_code == 422
    data = resp.json()
    assert data["code"] == "invalid_input" and field in data["fields"]


def test_household_of_twenty_is_allowed():
    resp = client.post("/api/eligibility", json={"hospital_slug": "fort-healthcare-inc", "household_size": 20,
                                                 "annual_income": 50000, "state": "WI"})
    assert resp.status_code == 200
