"""B's rules engine through A's bridge + API, with the real 2026 HHS table (data/fpl_2026.json)."""

import csv
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend import app as app_module
from backend import fpl, policies
from backend.eligibility import load_fpl_table_from_json, policy_rules_to_hospital_policy, run_eligibility
from backend.policy_reader.schema import PolicyRules
from backend.tests.test_policy_reader import FIXTURE

client = TestClient(app_module.app)
REAL = fpl.load_table(fpl.DEFAULT_TABLE_PATH)
RESOLVER = load_fpl_table_from_json(REAL)
RULES = PolicyRules.model_validate_json(FIXTURE.read_text())  # free <=200, 200.01-300 75% off, 300.01-400 AGB, OH residency


def post(**body):
    base = {"hospital_slug": "fort-healthcare-inc", "household_size": 2, "annual_income": 20000, "state": "WI"}
    resp = client.post("/api/eligibility", json={**base, **body})
    return resp, resp.json()


# ---------- boundaries with the real 2026 table ----------

def test_household_of_two_at_exactly_200_percent_is_free():
    resp, body = post(annual_income=43280)
    assert resp.status_code == 200, body
    assert body["data"]["percent_of_fpl"] == 200.0
    assert body["data"]["status"] == "likely_free"


def test_one_dollar_over_200_percent_is_discounted():
    _, body = post(annual_income=43281)
    assert body["data"]["status"] == "likely_discounted"
    assert {"fpl_min_percent", "fpl_max_percent", "discount_type", "value", "description"} <= set(body["data"]["tier"])  # C UI shape


def test_fixture_policy_ohio_boundary_direct():
    r = run_eligibility(RULES, 2, 43280.0, "OH", RESOLVER, fpl_year=2026, residency_state="OH")
    assert r.status.value == "likely_free"
    r = run_eligibility(RULES, 2, 43281.0, "OH", RESOLVER, fpl_year=2026, residency_state="OH")
    assert r.status.value == "likely_discounted" and r.matching_tier.discount_percent == 75


@pytest.mark.parametrize("size,state,expected", [(1, "WI", "15960"), (9, "WI", "61400"), (1, "AK", "19950"), (1, "HI", "18360"), (20, "WI", "123880")])
def test_fpl_used_for_size_and_state(size, state, expected):
    _, body = post(household_size=size, state=state, annual_income=1000)
    assert body["data"]["fpl_used"] == expected


def test_fpl_year_is_2026_not_null_regression():
    _, body = post()
    data = body["data"]
    assert data["fpl_year"] == 2026
    assert data["fpl_evidence"]["year"] == 2026


def test_missing_income_is_rejected():
    resp = client.post("/api/eligibility", json={"hospital_slug": "fort-healthcare-inc", "household_size": 2, "state": "WI"})
    assert resp.status_code == 422


def test_bad_inputs_rejected():
    assert post(household_size=0)[0].status_code == 422
    assert post(annual_income=-5)[0].status_code == 422
    assert post(hospital_slug="../etc")[0].status_code == 400
    assert post(hospital_slug="no-such-hospital")[0].status_code == 404


# ---------- response contract (frontend/lib/types.ts) ----------

def test_response_has_ui_keys_and_disclaimer():
    _, body = post()
    data = body["data"]
    assert data["status"] in {"likely_free", "likely_discounted", "probably_not_eligible", "cannot_determine"}
    assert data["disclaimer"] == "Likely eligible, not a guarantee."
    assert {"quote", "page", "verified", "status", "source_url"} <= set(data["evidence"])
    assert data["source_url"].startswith("https://")
    assert data["engine"] == "rules"


def test_caveats_use_plain_words_not_field_names():
    _, body = post(hospital_slug="usa-health", state="AL", annual_income=20000, assets_usd=0)
    text = " ".join(body["data"]["caveats"])
    assert "application_window" not in text and "asset_test" not in text


# ---------- conditions ----------

def test_asset_test_without_assets_cannot_determine_then_free_with_assets():
    _, body = post(hospital_slug="usa-health", state="AL", annual_income=20000)
    assert body["data"]["status"] == "cannot_determine"
    assert body["data"]["missing_facts"]
    _, body = post(hospital_slug="usa-health", state="AL", annual_income=20000, assets_usd=0)
    assert body["data"]["status"] == "likely_free"


def test_unclear_rule_is_unresolved_not_a_pass():
    rules, _ = policies.load_policy("adena-health-system")
    assert rules.asset_test.evidence.status == "unclear"
    _, body = post(hospital_slug="adena-health-system", state="OH", annual_income=20000, assets_usd=0)
    assert body["data"]["status"] == "cannot_determine"


def test_not_stated_adds_no_condition():
    rules, _ = policies.load_policy("baptist-memorial-health-care-corporation")
    names = {c.name for t in policy_rules_to_hospital_policy(rules).tiers for c in t.conditions}
    assert not any("residen" in n or "asset" in n for n in names)


def test_residency_outside_area_not_free():
    _, body = post(state="IL", residency_state="IL")
    assert body["data"]["status"] != "likely_free"


def test_income_table_without_percent_cannot_determine():
    data = RULES.model_dump()
    data["uses_income_table"] = True
    data["free_care"]["fpl_max_percent"] = None
    data["discount"]["fpl_max_percent"] = None
    data["discount"]["tiers"] = []
    rules = PolicyRules.model_validate(data)
    from backend.eligibility import eligibility_result_to_api_response

    r = run_eligibility(rules, 2, 20000.0, "OH", RESOLVER, fpl_year=2026, residency_state="OH")
    out = eligibility_result_to_api_response(r, rules, 92.4, None)
    assert out["status"] == "cannot_determine" and "dollar table" in out["explanation"]


def test_open_ended_tier_is_skipped():
    rules, _ = policies.load_policy("baptist-memorial-health-care-corporation")
    tiers = policy_rules_to_hospital_policy(rules).tiers
    assert all(t.threshold_value > 0 for t in tiers)


@pytest.mark.parametrize("slug", [h["slug"] for h in policies.build_index()])
@pytest.mark.parametrize("income", [0, 30000, 60000, 500000])
def test_every_cached_policy_runs_through_adapter(slug, income):
    rules, _ = policies.load_policy(slug)
    state = rules.hospital_state if rules.hospital_state and len(rules.hospital_state) == 2 else "WI"
    resp, body = post(hospital_slug=slug, state=state, annual_income=income, assets_usd=0)
    assert resp.status_code == 200, body


# ---------- hospital matching ----------

SAMPLE_KEY = Path(__file__).resolve().parents[2] / "sample_bills" / "answer_key.csv"


@pytest.mark.skipif(not SAMPLE_KEY.exists(), reason="C's sample bills not present")
def test_every_sample_bill_hospital_matches_its_policy():
    with SAMPLE_KEY.open() as fh:
        for row in csv.DictReader(fh):
            m = policies.match_hospital(row["hospital_name"], row["hospital_address"])
            assert m["matched"] and m["slug"] == row["hospital_slug"], (row["file"], m)


def test_alias_and_unknown_hospital():
    assert policies.match_hospital("OCH Regional Medical Center", "400 Hospital Rd, Starkville, MS 39759")["slug"] == "baptist-memorial-health-care-corporation"
    miss = policies.match_hospital("Mercy General Hospital", "1 Main St, Sacramento, CA 95819")
    assert miss["matched"] is False and miss["reason"]


def test_state_mismatch_lowers_score():
    same = policies.match_hospital("Fort HealthCare", "811 Cedar Bluff Rd, Fort Atkinson, WI 53538")["score"]
    other = policies.match_hospital("Fort HealthCare", "1 Elm St, Austin, TX 73301")
    assert other["score"] < same and other["matched"] is False


def test_api_hospitals_list_and_match():
    body = client.get("/api/hospitals").json()
    assert body["success"] and {"slug", "name", "state"} <= set(body["data"][0])
    body = client.post("/api/hospitals/match", json={"hospital_name": "USA Health", "hospital_address": "Mobile, AL 36617"}).json()
    assert body["data"]["slug"] == "usa-health"
