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
    resp = client.post("/api/eligibility", json={"hospital_slug": "usa-health", "household_size": 1, "annual_income": 15000, "state": "AL", "assets_usd": 0})
    body = resp.json()
    assert resp.status_code == 200, body
    data = body["data"]
    assert data["status"] == "likely_free" and data["percent_of_fpl"] == 150.0
    assert data["disclaimer"] == "Likely eligible — not a guarantee"
    assert data["source_url"] and data["evidence"]["page"]


def test_api_eligibility_validates_input():
    resp = client.post("/api/eligibility", json={"hospital_slug": "usa-health", "household_size": 0, "annual_income": 1, "state": "AL"})
    assert resp.status_code == 422


def test_e2e_real_engine_with_usa_health(monkeypatch):
    """End-to-end test: real engine + cached usa-health policy + fpl_test_table.json

    usa-health cached policy (cache/policies/usa-health__6a0883be.json):
    - free_care: fpl_max_percent=200
    - discount tiers: 200-300 @ 85% off, 300-400 @ 75% off
    - asset_test.applies=true
    - residency.required=true (area: "AL")
    """
    # Override FPL table to use test fixture
    monkeypatch.setattr(fpl, "_default_table", lambda: FAKE_FPL)

    # Test case 1: Income at 150% FPL (below 200% free care threshold) -> likely_free
    # For household_size=1 in contiguous, FPL = 10000, 150% = 15000
    # usa-health residency is AL, asset_test applies
    resp = client.post("/api/eligibility", json={
        "hospital_slug": "usa-health",
        "household_size": 1,
        "annual_income": 15000,
        "state": "AL",
        "assets_usd": 0,
        "residency_state": "AL"
    })
    assert resp.status_code == 200
    body = resp.json()
    data = body["data"]
    assert data["status"] == "likely_free"
    assert data["percent_of_fpl"] == 150.0
    assert data["disclaimer"] == "Likely eligible — not a guarantee"

    # Test case 2: Income at 250% FPL (in discount tier 200-300) -> likely_discounted
    resp = client.post("/api/eligibility", json={
        "hospital_slug": "usa-health",
        "household_size": 1,
        "annual_income": 25000,
        "state": "AL",
        "assets_usd": 0,
        "residency_state": "AL"
    })
    assert resp.status_code == 200
    body = resp.json()
    data = body["data"]
    assert data["status"] == "likely_discounted"
    assert data["tier"] is not None
    assert data["tier"]["type"] == "discounted"
    assert float(data["tier"]["discount_percent"]) == 85.0  # usa-health tier 200-300 is 85% off

    # Test case 3: Income above discount limit (500% FPL) -> probably_not_eligible
    resp = client.post("/api/eligibility", json={
        "hospital_slug": "usa-health",
        "household_size": 1,
        "annual_income": 50000,
        "state": "AL",
        "assets_usd": 0,
        "residency_state": "AL"
    })
    assert resp.status_code == 200
    body = resp.json()
    data = body["data"]
    assert data["status"] == "probably_not_eligible"

    # Test case 4: Missing assets when asset_test applies -> needs_more_information
    resp = client.post("/api/eligibility", json={
        "hospital_slug": "usa-health",
        "household_size": 1,
        "annual_income": 15000,
        "state": "AL",
        "residency_state": "AL"
        # assets_usd omitted
    })
    assert resp.status_code == 200
    body = resp.json()
    data = body["data"]
    # Without assets_usd, asset_test condition is UNKNOWN -> needs_more_information
    assert data["status"] == "needs_more_information"
    assert "assets" in str(data["missing_facts"]).lower() or "asset" in str(data["missing_facts"]).lower()

    # Test case 5: Wrong residency state -> still likely_free (usa-health has residency.required: null)
    # The cached usa-health policy does NOT require residency (required: null)
    # So wrong residency doesn't affect eligibility
    resp = client.post("/api/eligibility", json={
        "hospital_slug": "usa-health",
        "household_size": 1,
        "annual_income": 15000,
        "state": "AL",
        "assets_usd": 0,
        "residency_state": "OH"  # usa-health doesn't require residency
    })
    assert resp.status_code == 200
    body = resp.json()
    data = body["data"]
    assert data["status"] == "likely_free"
    assert data["percent_of_fpl"] == 150.0


def test_e2e_sample_rules_direct(monkeypatch):
    """Test real engine directly with sample_rules.json fixture (bypasses cache)

    sample_rules.json:
    - free_care: fpl_max_percent=200
    - discount tiers: 200.01-300 @ 75% off, 300.01-400 @ AGB
    - asset_test.applies=false
    - residency.required=true, area="State of Ohio", hospital_state="OH"
    """
    from backend.eligibility import run_eligibility, load_fpl_table_from_json
    from backend.policy_reader.schema import PolicyRules
    from pathlib import Path

    # Load fixtures
    fixture_path = Path(__file__).parent / "fixtures" / "sample_rules.json"
    rules = PolicyRules.model_validate_json(fixture_path.read_text())
    fpl_resolver = load_fpl_table_from_json(str(Path(__file__).parent / "fixtures" / "fpl_test_table.json"))

    # Test: 150% FPL (household 1, income 15000, FPL=10000) -> likely_free
    result = run_eligibility(rules, 1, 15000.0, "OH", fpl_resolver=fpl_resolver, assets_usd=5000, residency_state="OH")
    assert result.status.value == "likely_free"
    assert result.matching_tier.tier_id == "free"

    # Test: 250% FPL (household 1, income 25000) -> likely_discounted, 75% off
    result = run_eligibility(rules, 1, 25000.0, "OH", fpl_resolver=fpl_resolver, assets_usd=5000, residency_state="OH")
    assert result.status.value == "likely_discounted"
    assert result.matching_tier.discount_percent == 75

    # Test: 350% FPL (household 1, income 35000) -> likely_discounted, AGB
    result = run_eligibility(rules, 1, 35000.0, "OH", fpl_resolver=fpl_resolver, assets_usd=5000, residency_state="OH")
    assert result.status.value == "likely_discounted"
    assert result.matching_tier.discount_formula == "Amount Generally Billed (AGB)"

    # Test: 450% FPL (household 1, income 45000) -> probably_not_eligible
    result = run_eligibility(rules, 1, 45000.0, "OH", fpl_resolver=fpl_resolver, assets_usd=5000, residency_state="OH")
    assert result.status.value == "probably_not_eligible"

    # Test: Missing residency (residency_state doesn't match) -> needs_more_information
    # Residency mismatch returns NOT_SATISFIED -> goes to unresolved_rules, not missing_facts
    result = run_eligibility(rules, 1, 15000.0, "OH", fpl_resolver=fpl_resolver, assets_usd=5000, residency_state="CA")
    assert result.status.value == "needs_more_information"
    assert any("residency" in ur.lower() for ur in result.unresolved_rules)
