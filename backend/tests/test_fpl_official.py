"""data/fpl_2026.json must equal the official 2026 HHS poverty guidelines.

Values copied by hand from https://aspe.hhs.gov/topics/poverty-economic-mobility/poverty-guidelines
("HHS Poverty Guidelines for 2026"), read 2026-11-23; published in the Federal Register, doc 2026-00755, Jan 15, 2026.
Kept here, separate from the data file, so a typo in either one fails this test.
"""

import pytest

from backend import fpl

OFFICIAL_2026 = {
    "contiguous": ({1: 15960, 2: 21640, 3: 27320, 4: 33000, 5: 38680, 6: 44360, 7: 50040, 8: 55720}, 5680),
    "AK": ({1: 19950, 2: 27050, 3: 34150, 4: 41250, 5: 48350, 6: 55450, 7: 62550, 8: 69650}, 7100),
    "HI": ({1: 18360, 2: 24890, 3: 31420, 4: 37950, 5: 44480, 6: 51010, 7: 57540, 8: 64070}, 6530),
}
STATE_FOR_ROW = {"contiguous": "WI", "AK": "AK", "HI": "HI"}


def test_data_file_is_the_2026_table():
    table = fpl.load_table()
    assert table["year"] == 2026
    assert "2026-00755" in table["source_url"]


@pytest.mark.parametrize("row", sorted(OFFICIAL_2026))
def test_base_rows_match_official_values(row):
    base, add_on = OFFICIAL_2026[row]
    table = fpl.load_table()["tables"][row]
    assert {int(k): v for k, v in table["base"].items()} == base
    assert table["additional_person"] == add_on


@pytest.mark.parametrize("row", sorted(OFFICIAL_2026))
@pytest.mark.parametrize("size", [9, 12, 20])
def test_households_over_eight_use_the_official_increment(row, size):
    base, add_on = OFFICIAL_2026[row]
    assert fpl.poverty_line(size, STATE_FOR_ROW[row]) == base[8] + (size - 8) * add_on
