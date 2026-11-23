import builtins
import io
from pathlib import Path

import pdfplumber
import pytest

from backend.eob_reader.letters import build_insurance_letter


def text(data: bytes) -> str:
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        return " ".join(" ".join((p.extract_text() or "") for p in pdf.pages).split())


@pytest.fixture
def no_writes(monkeypatch):
    real_open = builtins.open

    def guarded(file, mode="r", *args, **kwargs):
        if any(c in mode for c in "wax+"):
            raise AssertionError(f"wrote {file}")
        return real_open(file, mode, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", guarded)
    monkeypatch.setattr(Path, "write_bytes", lambda *a, **k: (_ for _ in ()).throw(AssertionError("write")))


@pytest.mark.parametrize(("lang", "phrase"), [("en", "itemized hospital bill"), ("es", "factura hospitalaria detallada")])
def test_itemized_letter_builds_in_both_languages(lang, phrase, no_writes):
    pdf = build_insurance_letter(
        kind="itemized_bill",
        lang=lang,
        hospital="Sample Hospital",
        account_number="FAKE-1",
        service_date="2026-03-14",
        bill_amount="$250.00",
        eob_patient_responsibility="$200.00",
        claim_status="paid",
    )
    assert phrase in text(pdf).lower()


def test_hold_letter_is_request_not_guarantee():
    pdf = build_insurance_letter(
        kind="billing_hold",
        lang="en",
        hospital="Sample Hospital",
        account_number="FAKE-1",
        service_date="2026-03-14",
        bill_amount="$250.00",
        eob_patient_responsibility="$200.00",
        claim_status="pending",
    )
    value = text(pdf)
    assert "asking" in value and "request" in value and "not a statement" in value and "guaranteed" in value

