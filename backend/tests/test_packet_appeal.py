"""Appeal letter ("If they say no") and the optional benefit-letter checklist line. Built in memory, EN/ES."""

import pytest
from fastapi.testclient import TestClient

from backend import app as app_module
from backend.tests.test_packet import BODY, QUOTE, no_file_writes, pdf_text  # noqa: F401 - fixture import

client = TestClient(app_module.app)


def flat(data: bytes) -> str:
    return " ".join(" ".join(pdf_text(data)).split())


@pytest.mark.parametrize(("lang", "word"), [("en", "reconsider"), ("es", "reconsiderar")])
def test_appeal_pdf_builds_in_both_languages(lang, word, no_file_writes):  # noqa: F811
    resp = client.post("/api/packet", json={**BODY, "lang": lang, "kind": "appeal"})
    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"] == "application/pdf"
    assert 'filename="BillBack-appeal-fort-healthcare-inc.pdf"' in resp.headers["content-disposition"]
    text = flat(resp.content)
    assert word in text.lower()
    assert "FAKE998877" in text
    assert "200% of the FPL qualify for a 100% discount" in text
    assert "110%" in text


def test_appeal_asks_for_reasons_in_writing_and_keeps_footer():
    text = flat(client.post("/api/packet", json={**BODY, "lang": "en", "kind": "appeal"}).content)
    assert "Date of the decision" in text
    assert "I believe I qualify because" in text
    assert "reasons for it in writing" in text
    assert "Likely eligible, not a guarantee." in text


def test_default_kind_is_still_the_application():
    resp = client.post("/api/packet", json={**BODY, "lang": "en"})
    assert 'filename="BillBack-application-fort-healthcare-inc.pdf"' in resp.headers["content-disposition"]
    assert "reconsider" not in flat(resp.content).lower()


def test_bad_kind_is_422():
    assert client.post("/api/packet", json={**BODY, "kind": "lawsuit"}).status_code == 422


@pytest.mark.parametrize(("lang", "phrase"), [("en", "SNAP, Medicaid or WIC benefit letter"), ("es", "carta del beneficio de SNAP, Medicaid o WIC")])
def test_benefit_letter_on_checklist_only_when_asked(lang, phrase):
    with_letter = flat(client.post("/api/packet", json={**BODY, "lang": lang, "benefits": True}).content)
    without = flat(client.post("/api/packet", json={**BODY, "lang": lang}).content)
    assert phrase in with_letter
    assert phrase not in without
