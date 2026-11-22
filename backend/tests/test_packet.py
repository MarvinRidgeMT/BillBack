"""Application packet PDF: builds in EN and ES, carries the account number and the policy quote, never writes a file."""

import builtins
import io
import os
from pathlib import Path

import pdfplumber
import pytest
from fastapi.testclient import TestClient

from backend import app as app_module
from backend import packet

client = TestClient(app_module.app)
QUOTE = "Patients at or below 200% of the FPL qualify for a 100% discount."
BODY = {
    "bill": {
        "hospital_name": "Fort HealthCare",
        "hospital_address": "611 Sherman Ave E, Fort Atkinson, WI 53538",
        "amount_due": "$389.10",
        "service_date": "Feb 2, 2026",
        "account_number": "FAKE998877",
    },
    "hospital_slug": "fort-healthcare-inc",
    "household_size": 3,
    "annual_income": 30000,
    "eligibility": {"status": "likely_free", "percent_of_fpl": 110.2, "quote": QUOTE, "page": 1, "fpl_year": 2026},
}


def pdf_text(data: bytes) -> list[str]:
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        return [(page.extract_text() or "") for page in pdf.pages]


@pytest.fixture
def no_file_writes(monkeypatch):
    """Fail the test if anything opens a file for writing."""
    real_open = builtins.open

    def guarded(file, mode="r", *args, **kwargs):
        if any(ch in mode for ch in "wax+"):
            raise AssertionError(f"packet tried to write {file!r}")
        return real_open(file, mode, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", guarded)
    monkeypatch.setattr(Path, "write_bytes", lambda *a, **k: (_ for _ in ()).throw(AssertionError("write_bytes")))
    monkeypatch.setattr(Path, "write_text", lambda *a, **k: (_ for _ in ()).throw(AssertionError("write_text")))


@pytest.mark.parametrize("lang", ["en", "es"])
def test_packet_endpoint_returns_two_page_pdf(lang, no_file_writes):
    resp = client.post("/api/packet", json={**BODY, "lang": lang})
    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"] == "application/pdf"
    assert 'filename="BillBack-application-fort-healthcare-inc.pdf"' in resp.headers["content-disposition"]
    pages = pdf_text(resp.content)
    assert len(pages) == 2
    text = " ".join(" ".join(pages).split())
    assert "FAKE998877" in text
    assert "200% of the FPL qualify for a 100% discount" in text  # the quote stays in its original language
    assert "$389.10" in text


def test_english_letter_asks_to_pause_collections_and_has_checklist():
    pages = pdf_text(client.post("/api/packet", json={**BODY, "lang": "en"}).content)
    letter, checklist = (" ".join(p.split()) for p in pages)
    assert "pause all collection activity" in letter
    assert "110%" in letter and "Financial Assistance Policy" in letter
    assert "Patient name" in letter
    for item in ("photo ID", "pay stubs", "copy of this bill", "Make a copy", "30 days"):
        assert item in checklist
    assert "Likely eligible, not a guarantee. The hospital makes the final decision. Made with BillBack." in letter
    assert "Made with BillBack" in checklist


def test_spanish_letter_is_spanish():
    pages = pdf_text(client.post("/api/packet", json={**BODY, "lang": "es"}).content)
    text = " ".join(" ".join(pages).split())
    assert "Solicitud de asistencia financiera" in text
    assert "detengan toda gestión de cobro" in text
    assert "Hecho con BillBack" in text


def test_phone_comes_from_how_to_apply():
    assert packet.find_phone("Call 855-275-7408 or (740) 779-8786") == "855-275-7408"
    assert packet.find_phone(None) is None
    pdf = packet.build_packet(
        bill=BODY["bill"], hospital_name="X", household_size=1, annual_income=0, percent_of_fpl=0,
        fpl_year=2026, quote="", page=None, source_url=None, how_to_apply="Call (740) 779-8786", lang="en",
    )
    assert "(740) 779-8786" in " ".join(pdf_text(pdf))


def test_user_text_is_escaped_not_markup():
    bill = {**BODY["bill"], "account_number": "<b>1&2</b>"}
    pdf = packet.build_packet(
        bill=bill, hospital_name="A & B <Hospital>", household_size=2, annual_income=1, percent_of_fpl=1,
        fpl_year=2026, quote="", page=None, source_url=None, how_to_apply=None,
    )
    text = " ".join(pdf_text(pdf))
    assert "<b>1&2</b>" in text and "A & B <Hospital>" in text


def test_unknown_hospital_is_404_and_bad_lang_is_422():
    assert client.post("/api/packet", json={**BODY, "hospital_slug": "nope-nope"}).status_code == 404
    assert client.post("/api/packet", json={**BODY, "lang": "fr"}).status_code == 422
