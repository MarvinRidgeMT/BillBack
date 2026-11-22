import json
from pathlib import Path

import pytest

from backend import fpl

TABLE = fpl.load_table(Path(__file__).parent / "fixtures" / "fpl_test_table.json")


def test_household_of_one_contiguous():
    assert fpl.poverty_line(1, "OH", table=TABLE) == 10000


def test_household_of_eight():
    assert fpl.poverty_line(8, "TX", table=TABLE) == 38000


def test_household_of_nine_and_ten_use_add_on():
    assert fpl.poverty_line(9, "CA", table=TABLE) == 42000
    assert fpl.poverty_line(10, "CA", table=TABLE) == 46000


def test_alaska_and_hawaii_use_own_rows():
    assert fpl.poverty_line(1, "AK", table=TABLE) == 12500
    assert fpl.poverty_line(9, "ak", table=TABLE) == 52500
    assert fpl.poverty_line(2, "HI", table=TABLE) == 16100


def test_dc_uses_contiguous_row():
    assert fpl.poverty_line(3, "DC", table=TABLE) == 18000


def test_income_exactly_200_percent_and_one_dollar_over():
    assert fpl.percent_of_fpl(20000, 1, "OH", table=TABLE) == 200.0
    over = fpl.percent_of_fpl(20001, 1, "OH", table=TABLE)
    assert over > 200.0 and over < 200.02


def test_zero_income_is_zero_percent():
    assert fpl.percent_of_fpl(0, 4, "WI", table=TABLE) == 0.0


@pytest.mark.parametrize("size", [0, -1])
def test_rejects_household_below_one(size):
    with pytest.raises(ValueError, match="household_size"):
        fpl.poverty_line(size, "OH", table=TABLE)


def test_rejects_non_integer_household():
    with pytest.raises(ValueError, match="household_size"):
        fpl.poverty_line(2.5, "OH", table=TABLE)


def test_rejects_negative_income():
    with pytest.raises(ValueError, match="annual_income"):
        fpl.percent_of_fpl(-1, 2, "OH", table=TABLE)


def test_rejects_bad_state():
    with pytest.raises(ValueError, match="state"):
        fpl.poverty_line(1, "Ohio", table=TABLE)


def test_load_table_rejects_missing_rows(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"year": 2026, "tables": {"contiguous": {"base": {"1": 1}, "additional_person": 1}}}))
    with pytest.raises(ValueError):
        fpl.load_table(bad)


def test_real_table_if_present_is_complete():
    real = Path(fpl.DEFAULT_TABLE_PATH)
    if not real.exists():
        pytest.skip("data/fpl_2026.json not added yet (HHS page was down)")
    table = fpl.load_table(real)
    assert table["year"] == 2026
    assert table["source_url"].startswith("https://")
