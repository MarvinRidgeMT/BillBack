"""Policy receipt (page image + quote boxes), thresholds and policy facts. Public policy files only; no AI."""

from fastapi.testclient import TestClient

from backend.app import app
from backend import policy_page

client = TestClient(app)

FORT = "fort-healthcare-inc"
FORT_QUOTE = (
    "Persons whose income is at or up to 200% of the guidelines will be considered for complete "
    "forgiveness of their outstanding bill."
)


def test_normalize_collapses_whitespace_quotes_and_hyphenation():
    assert policy_page.normalize("“Hello”   wo-\nrld’s") == '"Hello" world\'s'


def test_fort_demo_quote_is_found_with_boxes():
    res = client.get("/api/policy/page", params={"slug": FORT, "page": 1, "quote": FORT_QUOTE})
    assert res.status_code == 200
    body = res.json()["data"]
    assert body["found"] is True
    assert len(body["boxes"]) >= 1
    assert body["image"].startswith("data:image/png;base64,")
    for box in body["boxes"]:
        assert 0 <= box["x0"] < box["x1"] <= body["width"]
        assert 0 <= box["y0"] < box["y1"] <= body["height"]


def test_made_up_quote_is_not_found_and_has_no_boxes():
    res = client.get(
        "/api/policy/page",
        params={"slug": FORT, "page": 1, "quote": "Purple elephants receive free parking on alternate Tuesdays forever."},
    )
    assert res.status_code == 200
    body = res.json()["data"]
    assert body["found"] is False
    assert body["boxes"] == []


def test_bad_slug_is_404():
    assert client.get("/api/policy/page", params={"slug": "no-such-hospital", "page": 1, "quote": "x"}).status_code == 404


def test_invalid_slug_is_400():
    assert client.get("/api/policy/page", params={"slug": "../etc", "page": 1, "quote": "x"}).status_code == 400


def test_page_out_of_range_is_404():
    assert client.get("/api/policy/page", params={"slug": FORT, "page": 999, "quote": "x"}).status_code == 404


def test_thresholds_for_fort():
    res = client.get("/api/policy/thresholds", params={"slug": FORT, "household_size": 3, "state": "WI"})
    assert res.status_code == 200
    body = res.json()["data"]
    assert body["poverty_line"] == 15960 + 2 * 5680
    assert body["free_max_percent"] == 200
    assert body["max_percent"] == 400


def test_facts_for_fort():
    res = client.get("/api/policy/facts", params={"slug": FORT})
    assert res.status_code == 200
    body = res.json()["data"]
    assert body["hospital_state"] == "WI"
    assert body["application_window"]["days"] == 240
    assert body["application_window"]["counted_from"] == "first_post_discharge_billing_statement"
    assert "presumptive" in body["presumptive_eligibility"].lower()
    assert body["has_page_images"] is True


def test_facts_state_law_for_washington_hospital():
    body = client.get("/api/policy/facts", params={"slug": "uw-medicine-harborview-medical-center-uw-medical-center-airl"}).json()["data"]
    assert body["hospital_state"] == "WA"
    assert body["state_law"]["citation"] == "RCW 70.170.060"
    assert body["state_law"]["url"].startswith("https://")


def test_facts_no_state_law_for_wisconsin():
    assert client.get("/api/policy/facts", params={"slug": FORT}).json()["data"]["state_law"] is None


def test_banner_state_comes_from_index():
    assert client.get("/api/policy/facts", params={"slug": "banner-health"}).json()["data"]["hospital_state"] == "AZ"


def test_state_laws_file_is_complete():
    from backend import policy_facts

    for row in policy_facts._state_laws().values():
        for key in ("state", "name_en", "name_es", "summary_en", "summary_es", "citation", "url", "checked_on"):
            assert row[key], (row["state"], key)


def test_hospitals_list_has_limits_for_the_map():
    rows = client.get("/api/hospitals").json()["data"]
    fort = next(r for r in rows if r["slug"] == FORT)
    assert fort["free_max_percent"] == 200
    assert fort["discount_max_percent"] == 400
    assert fort["source_url"].startswith("https://")
    assert all({"slug", "name", "state", "free_max_percent", "discount_max_percent"} <= set(r) for r in rows)
