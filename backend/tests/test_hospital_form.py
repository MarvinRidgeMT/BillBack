"""The hospital's own application form, added to the packet when we have it on file. Public form; nothing written."""

import io
from datetime import date

import pypdf
import pytest
from fastapi.testclient import TestClient

from backend import app as app_module
from backend import hospital_form
from backend.tests.test_packet import BODY, no_file_writes, pdf_text  # noqa: F401 - fixture import

client = TestClient(app_module.app)
MARSHFIELD = "marshfield-clinic-health-system"
M_BODY = {**BODY, "hospital_slug": MARSHFIELD, "bill": {**BODY["bill"], "hospital_name": "Marshfield Clinic"}}


def test_form_on_file_for_marshfield_in_both_languages():
    assert hospital_form.form_for(MARSHFIELD, "en").fillable is True
    assert hospital_form.form_for(MARSHFIELD, "es") is not None
    assert hospital_form.form_for("fort-healthcare-inc", "en") is None
    assert hospital_form.form_for("../etc", "en") is None


def test_fill_only_sets_the_signature_date():
    form = hospital_form.form_for(MARSHFIELD, "en")
    filled = pypdf.PdfReader(io.BytesIO(hospital_form.filled_form(form, today=date(2026, 11, 22))))
    values = {k: v.get("/V") for k, v in (filled.get_fields() or {}).items()}
    assert (values["Text43"], values["undefined"], values["undefined_2"]) == ("11", "22", "2026")
    for blank in ("Guarantor name", "Social Security", "Address city state and ZIP", "Phone", "DOB", "NameRow1"):
        assert not values.get(blank), blank


@pytest.mark.parametrize("lang", ["en", "es"])
def test_packet_includes_the_hospitals_own_form(lang, no_file_writes):  # noqa: F811
    resp = client.post("/api/packet", json={**M_BODY, "lang": lang})
    assert resp.status_code == 200, resp.text
    pages = pdf_text(resp.content)
    own = 2 if lang == "en" else 5
    assert len(pages) == 2 + own
    checklist = " ".join(pages[1].split())
    assert ("Marshfield Clinic's own application form" in checklist) if lang == "en" else ("formulario de solicitud de Marshfield Clinic" in checklist)
    assert "Financial Assistance Application" in " ".join(pages[2:])


def test_english_form_stays_fillable_after_merge():
    resp = client.post("/api/packet", json={**M_BODY, "lang": "en"})
    fields = pypdf.PdfReader(io.BytesIO(resp.content)).get_fields() or {}
    assert "Guarantor name" in fields and "Signature" in fields


def test_packet_without_a_form_on_file_is_unchanged():
    pages = pdf_text(client.post("/api/packet", json={**BODY, "lang": "en"}).content)
    assert len(pages) == 2
    assert "application form, if it has one" in " ".join(pages[1].split())


def test_appeal_does_not_include_the_form():
    assert len(pdf_text(client.post("/api/packet", json={**M_BODY, "kind": "appeal"}).content)) == 2


def test_facts_say_whether_the_form_is_included():
    assert client.get("/api/policy/facts", params={"slug": MARSHFIELD}).json()["data"]["own_form"] is True
    assert client.get("/api/policy/facts", params={"slug": "fort-healthcare-inc"}).json()["data"]["own_form"] is False
