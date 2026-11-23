"""Rules-engine edge cases with the real 2026 table, through the API (plain code, no AI).

Exactly 200%, $1 over, household of 1, 8 and 9+ (per-person increment), zero and missing income, AK/HI rows,
and the free <= discount invariant on every cached policy.
"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend import fpl
from backend.app import app
from backend.policy_reader.cache import DEFAULT_CACHE_DIR
from backend.policy_reader.schema import PolicyRules

client = TestClient(app)
# Fort HealthCare: free <= 200% FPL, sliding-scale discount to 400%, WI residency, no asset test (cache/policies).
SLUG, STATE = "fort-healthcare-inc", "WI"


def check(size: int, income: float, state: str = STATE, slug: str = SLUG) -> dict:
    resp = client.post("/api/eligibility", json={"hospital_slug": slug, "household_size": size,
                                                 "annual_income": income, "state": state})
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]


@pytest.mark.parametrize("size", [1, 2, 4, 8, 9, 12])
def test_exactly_200_percent_is_free_and_one_dollar_over_is_not(size):
    line = fpl.poverty_line(size, STATE)
    at = check(size, 2 * line)
    assert at["percent_of_fpl"] == 200.0 and at["status"] == "likely_free"
    over = check(size, 2 * line + 1)
    assert over["status"] == "likely_discounted"


def test_household_of_one_uses_the_one_person_line():
    assert check(1, 15960)["fpl_used"] == "15960"


def test_household_of_eight_is_the_last_table_row():
    assert check(8, 10000)["fpl_used"] == "55720"


@pytest.mark.parametrize("size,expected", [(9, 61400), (10, 67080), (20, 123880)])
def test_households_over_eight_add_5680_per_person(size, expected):
    assert check(size, 10000)["fpl_used"] == str(expected)


def test_zero_income_is_zero_percent_and_free():
    data = check(3, 0)
    assert data["percent_of_fpl"] == 0.0 and data["status"] == "likely_free"


def test_missing_income_is_rejected_not_treated_as_zero():
    resp = client.post("/api/eligibility", json={"hospital_slug": SLUG, "household_size": 3, "state": STATE})
    assert resp.status_code == 422


def test_just_over_the_top_discount_limit_is_not_eligible():
    assert check(2, 4 * fpl.poverty_line(2, STATE) + 1)["status"] == "probably_not_eligible"


@pytest.mark.parametrize("state,size,line", [("AK", 1, 19950), ("AK", 9, 76750), ("HI", 4, 37950), ("HI", 9, 70600)])
def test_alaska_and_hawaii_use_their_own_rows(state, size, line):
    # usa-health has no residency rule, so an AK/HI household isn't ruled out; assets satisfy its asset test.
    resp = client.post("/api/eligibility", json={"hospital_slug": "usa-health", "household_size": size,
                                                 "annual_income": 1000, "state": state, "assets_usd": 0})
    assert resp.json()["data"]["fpl_used"] == str(line)


def _cached_rules() -> list[tuple[str, PolicyRules]]:
    return [(p.name, PolicyRules.model_validate_json(p.read_text()))
            for p in sorted(Path(DEFAULT_CACHE_DIR).glob("*__*.json"))]


@pytest.mark.parametrize("name,rules", _cached_rules(), ids=lambda v: v if isinstance(v, str) else "")
def test_free_limit_never_above_discount_limit(name, rules):
    """Every cached policy: free-care limit <= discount limit and <= every discount tier's upper limit,
    OR the policy is flagged for a person to check (never silently used).

    Found by this test on 2026-11-23: Novant gives uninsured patients free care to 300% but its tiers (200-250%,
    250-300%) are for insured residents; the schema has one free limit, so the reader flagged both fields.
    """
    free = rules.free_care.fpl_max_percent
    if free is None:
        pytest.skip("policy states no free-care % (income table)")
    limits = [rules.discount.fpl_max_percent] + [t.fpl_max_percent for t in rules.discount.tiers]
    broken = [x for x in limits if x is not None and free > x]
    if broken:
        assert rules.needs_human_review and {"free_care", "discount"} & set(rules.review_fields), (
            f"{name}: free {free}% is above discount limit(s) {broken} and the policy is not flagged"
        )
