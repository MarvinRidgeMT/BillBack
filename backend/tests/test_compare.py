"""eval/compare.py: the field comparison rules every eval uses."""

from datetime import date

import pytest

from eval import compare


def test_text_normalizes_whitespace_case_and_quotes():
    assert compare.text_equal("  USA   Health\n", "usa health")
    assert compare.text_equal("Children’s Hospital", "children's hospital")
    assert not compare.text_equal("USA Health", "USA Health System")


@pytest.mark.parametrize("got,expected", [("$4,812.00", 481200), ("4812", "4812.00"), ("$ 4812.0", "$4,812"), (481200, "4812.00")])
def test_money_matches_to_the_cent(got, expected):
    assert compare.money_equal(got, expected)


@pytest.mark.parametrize("got,expected", [("$4,812.01", "4812.00"), ("4812", "481.20"), (None, "0"), ("about $4,800", "4800")])
def test_money_one_cent_off_or_unparseable_is_wrong(got, expected):
    assert not compare.money_equal(got, expected)


def test_fraction_of_a_cent_is_not_money():
    assert compare.parse_cents("12.345") is None


@pytest.mark.parametrize("got", ["2026-08-14", "08/14/2026", "8/14/26", "Aug 14, 2026", "August 14 2026", date(2026, 8, 14)])
def test_dates_match_after_parsing(got):
    assert compare.date_equal(got, "2026-08-14")


def test_wrong_or_unparseable_date():
    assert not compare.date_equal("2026-08-15", "2026-08-14")
    assert not compare.date_equal("next Tuesday", "2026-08-14")
    assert not compare.date_equal(None, None)


def test_hospital_name_exact_after_normalization():
    assert compare.name_match("Fort HealthCare.", "fort healthcare")


def test_hospital_name_fuzzy_threshold_is_point_nine():
    assert compare.NAME_FUZZY_THRESHOLD == 0.90
    assert compare.name_match("Boys Town National Research Hospitl", "Boys Town National Research Hospital")
    assert not compare.name_match("Boys Town Hospital", "Boys Town National Research Hospital")
    assert not compare.name_match("", "USA Health")


def test_address_word_order_tolerated_but_wrong_number_is_not():
    assert compare.name_match("1200 Magnolia Grove Blvd, Mobile, AL 36617", "1200 Magnolia Grove Blvd Mobile AL 36617")
    assert not compare.name_match("9 Main St, Mobile, AL 36617", "1200 Magnolia Grove Blvd, Mobile, AL 36617")


def test_one_digit_off_address_is_wrong_even_though_fuzzy_ratio_passes():
    """Found in review: token-sort ratio of these is ~0.91, so a fuzzy-only rule would count it correct."""
    assert compare.name_similarity("123 Main St, Mobile, AL 36617", "125 Main St, Mobile, AL 36617") >= 0.9
    assert not compare.compare_bill_field("hospital_address", "123 Main St, Mobile, AL 36617", "125 Main St, Mobile, AL 36617")
    assert not compare.compare_bill_field("hospital_address", "1200 Magnolia Grove Blvd, Mobile, AL 36618",
                                          "1200 Magnolia Grove Blvd, Mobile, AL 36617")
    assert compare.compare_bill_field("hospital_address", "1200 Magnolia Grove Blvd Mobile AL 36617",
                                      "1200 Magnolia Grove Blvd, Mobile, AL 36617")


def test_account_number_keeps_separators():
    assert compare.account_equal("fh 7720-1145", "FH 7720-1145")
    assert not compare.account_equal("FH77201145", "FH 7720-1145")
    assert not compare.account_equal("", "")


def test_fpl_percent_exact():
    assert compare.fpl_equal(200, 200.0)
    assert compare.fpl_equal("250", 250)
    assert not compare.fpl_equal(201, 200)
    assert compare.fpl_equal(None, None)
    assert not compare.fpl_equal(None, 200)


def test_bool_fields():
    assert compare.bool_equal("yes", True)
    assert compare.bool_equal(False, "no")
    assert not compare.bool_equal(None, "no")


def test_compare_bill_field_dispatch_and_unknown_field():
    assert compare.compare_bill_field("amount_due", 670000, "6700.00")
    assert compare.compare_bill_field("service_date", "10/03/2026", "2026-10-03")
    with pytest.raises(KeyError):
        compare.compare_bill_field("patient_name", "x", "x")
