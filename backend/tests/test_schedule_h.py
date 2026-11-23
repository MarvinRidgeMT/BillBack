from backend import schedule_h


def test_known_hospital_returns_sourced_record():
    record = schedule_h.for_hospital("adena-health-system")
    assert record is not None
    assert record["ein"] == "314379443"
    assert record["free_care_fpl_percent"] == 200
    assert record["tax_period"] == "202412"
    assert record["xml_path"].endswith("_public.xml")
    assert record["status"] == "agree"


def test_unknown_or_unmatched_hospital_has_no_badge():
    assert schedule_h.for_hospital("not-a-real-hospital") is None
