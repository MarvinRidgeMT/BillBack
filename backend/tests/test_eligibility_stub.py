from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend import app as app_module
from backend import eligibility_stub as stub
from backend import fpl
from backend.policy_reader.schema import PolicyRules
from backend.tests.test_policy_reader import FIXTURE

RULES = PolicyRules.model_validate_json(FIXTURE.read_text())  # free <=200, 201-300 75% off, 301-400 AGB
FAKE_FPL = fpl.load_table(Path(__file__).parent / "fixtures" / "fpl_test_table.json")


def test_at_or_below_free_limit_is_likely_free():
    r = stub.decide(200.0, RULES)
    assert r["status"] == "likely_free"
    assert r["evidence"]["quote"].startswith("Patients with household income at or below 200%")
    assert r["disclaimer"] == "Likely eligible — not a guarantee"


def test_in_discount_band_picks_tier():
    r = stub.decide(250.0, RULES)
    assert r["status"] == "likely_discounted"
    assert r["tier"]["value"] == 75


def test_gap_between_bands_goes_to_lower_matching_tier():
    assert stub.decide(200.5, RULES)["tier"]["fpl_max_percent"] == 300


def test_above_discount_limit_probably_not_eligible():
    assert stub.decide(400.01, RULES)["status"] == "probably_not_eligible"


def test_missing_thresholds_cannot_determine():
    data = RULES.model_dump()
    data["free_care"]["fpl_max_percent"] = None
    data["discount"]["fpl_max_percent"] = None
    data["discount"]["tiers"] = []
    assert stub.decide(150, PolicyRules.model_validate(data))["status"] == "cannot_determine"


@pytest.mark.parametrize("slug", ["../etc/passwd", "a/b", "", "x" * 100])
def test_policy_slug_rejects_paths(slug):
    with pytest.raises(ValueError):
        stub.load_policy(slug)


def test_load_cached_policy_by_slug():
    rules, path = stub.load_policy("usa-health")
    assert rules.hospital_name == "USA Health" and path.name.startswith("usa-health__")


client = TestClient(app_module.app)


def test_api_eligibility(monkeypatch):
    monkeypatch.setattr(fpl, "_default_table", lambda: FAKE_FPL)
    resp = client.post("/api/eligibility", json={"hospital_slug": "usa-health", "household_size": 1, "annual_income": 15000, "state": "AL"})
    body = resp.json()
    assert resp.status_code == 200, body
    data = body["data"]
    assert data["status"] == "likely_free" and data["percent_of_fpl"] == 150.0
    assert data["disclaimer"] == "Likely eligible — not a guarantee"
    assert data["source_url"] and data["evidence"]["page"]


def test_api_eligibility_validates_input():
    resp = client.post("/api/eligibility", json={"hospital_slug": "usa-health", "household_size": 0, "annual_income": 1, "state": "AL"})
    assert resp.status_code == 422
