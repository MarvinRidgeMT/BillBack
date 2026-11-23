import io
from datetime import date

import pdfplumber
import pytest
from fastapi.testclient import TestClient

from backend.app import app
from backend.follow_up import build_follow_up_letter


def text(data: bytes) -> str:
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        return " ".join(" ".join((page.extract_text() or "") for page in pdf.pages).split())


@pytest.mark.parametrize(("lang", "phrase"), [("en", "status update"), ("es", "actualización")])
def test_status_request_builds_en_es(lang, phrase):
    value = text(build_follow_up_letter(kind="status_request", lang=lang, hospital="Sample", account_number="FAKE", service_date="2026-01-02", today=date(2026, 11, 23)))
    assert phrase in value.lower()


def test_document_checklist_includes_only_known_choices():
    value = text(build_follow_up_letter(kind="more_documents", lang="en", hospital="Sample", account_number="FAKE", service_date="", documents=["income", "unknown", "insurance"]))
    assert "Proof of income" in value and "Insurance or coverage" in value and "unknown" not in value


@pytest.mark.parametrize("lang", ["en", "es"])
def test_collection_letter_is_request_not_guarantee_and_points_to_legal_aid(lang):
    value = text(build_follow_up_letter(kind="eca_pause_request", lang=lang, hospital="Sample", account_number="FAKE", service_date="" )).lower()
    if lang == "en":
        assert "request" in value and "not a guarantee" in value and "legal aid" in value and "501(r)(6)" in value
    else:
        assert "solicitud" in value and "no garantiza" in value and "ayuda legal" in value and "501(r)(6)" in value


def test_follow_up_endpoint_streams_private_pdf():
    response = TestClient(app).post("/api/follow-up/letter", json={"kind": "status_request", "lang": "en", "hospital": "Sample", "account_number": "FAKE", "service_date": "2026-01-02"})
    assert response.status_code == 200
    assert response.content.startswith(b"%PDF")
    assert response.headers["cache-control"] == "no-store"
