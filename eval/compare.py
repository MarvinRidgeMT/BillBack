"""Field comparison rules for every eval. One place, unit-tested in backend/tests/test_compare.py.

Rules (also printed in docs/RESULTS.md):
- text: Unicode-normalized, case-folded, whitespace collapsed, then compared exactly
- money: must match to the cent (parsed from "$1,234.50", "1234.5", or integer cents)
- dates: must be the same calendar day after parsing (ISO, US m/d/y, "Aug 14, 2026", ...)
- hospital names and addresses: equal after normalization, or fuzzy ratio >= NAME_FUZZY_THRESHOLD
- % of the poverty line: must match exactly (200 == 200.0; 200 != 201)
- yes/no fields: compared as booleans ("yes"/"true"/"y" -> True)
"""

from __future__ import annotations

import re
import unicodedata
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Optional, Union

from rapidfuzz import fuzz

NAME_FUZZY_THRESHOLD = 0.90  # stated in docs/RESULTS.md
_DATE_FORMATS = ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%m-%d-%Y", "%b %d, %Y", "%B %d, %Y", "%b %d %Y", "%B %d %Y",
                 "%d %b %Y", "%d %B %Y", "%b. %d, %Y")
_PUNCT = re.compile(r"[.,;:]")
_MONEY_RE = re.compile(r"^-?\$?\s*-?(\d{1,3}(,\d{3})+|\d+)(\.\d+)?$")
TRUE_WORDS = {"yes", "y", "true", "1"}
FALSE_WORDS = {"no", "n", "false", "0"}


def norm_text(value: Optional[str]) -> str:
    """NFKC, curly quotes straightened, lowercase, whitespace collapsed."""
    if value is None:
        return ""
    text = unicodedata.normalize("NFKC", str(value))
    text = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", text).strip().casefold()


def text_equal(got: Optional[str], expected: Optional[str]) -> bool:
    return norm_text(got) == norm_text(expected)


def parse_cents(value: Union[str, int, float, None]) -> Optional[int]:
    """'$1,234.50' / '1234.5' -> 123450. An int is taken as cents already. None if it isn't money."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int((Decimal(str(value)) * 100).quantize(Decimal("1")))
    text = str(value).strip().replace("USD", "").strip()
    if not _MONEY_RE.match(text):
        return None
    try:
        amount = Decimal(text.replace("$", "").replace(",", "").replace(" ", ""))
    except InvalidOperation:
        return None
    cents = amount * 100
    if cents != cents.to_integral_value():
        return None  # fractions of a cent are not money on a bill
    return int(cents)


def money_equal(got: Union[str, int, float, None], expected: Union[str, int, float, None]) -> bool:
    g, e = parse_cents(got), parse_cents(expected)
    return g is not None and g == e


def parse_date(value: Union[str, date, None]) -> Optional[date]:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    text = re.sub(r"\s+", " ", str(value).strip())
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def date_equal(got: Union[str, date, None], expected: Union[str, date, None]) -> bool:
    g, e = parse_date(got), parse_date(expected)
    return g is not None and g == e


def _name_key(value: Optional[str]) -> str:
    return re.sub(r"\s+", " ", _PUNCT.sub(" ", norm_text(value))).strip()


def name_similarity(got: Optional[str], expected: Optional[str]) -> float:
    """0-1. token_sort_ratio, so word order ("Health, USA" vs "USA Health") doesn't matter."""
    g, e = _name_key(got), _name_key(expected)
    if not g or not e:
        return 0.0
    return fuzz.token_sort_ratio(g, e) / 100


def name_match(got: Optional[str], expected: Optional[str], threshold: float = NAME_FUZZY_THRESHOLD) -> bool:
    if not _name_key(got) or not _name_key(expected):
        return False
    return _name_key(got) == _name_key(expected) or name_similarity(got, expected) >= threshold


def account_equal(got: Optional[str], expected: Optional[str]) -> bool:
    """Case- and whitespace-insensitive. Separators matter: 'FH 7720-1145' != 'FH77201145'."""
    return bool(norm_text(expected)) and norm_text(got) == norm_text(expected)


def fpl_equal(got: Union[int, float, str, None], expected: Union[int, float, str, None]) -> bool:
    """% of the poverty line: exact. None == None means both say 'not stated'."""
    if got is None or expected is None:
        return got is None and expected is None
    try:
        return Decimal(str(got)) == Decimal(str(expected))
    except InvalidOperation:
        return False


def parse_bool(value: Any) -> Optional[bool]:
    if isinstance(value, bool):
        return value
    word = norm_text(None if value is None else str(value))
    if word in TRUE_WORDS:
        return True
    if word in FALSE_WORDS:
        return False
    return None


def bool_equal(got: Any, expected: Any) -> bool:
    g, e = parse_bool(got), parse_bool(expected)
    return e is not None and g == e


BILL_FIELDS = ("hospital_name", "hospital_address", "amount_due", "service_date", "account_number")
_BILL_RULES = {
    "hospital_name": name_match,
    "hospital_address": name_match,
    "amount_due": money_equal,
    "service_date": date_equal,
    "account_number": account_equal,
}


def compare_bill_field(field: str, got: Any, expected: Any) -> bool:
    """One bill field. `got` is the extracted value (string, or normalized cents/ISO date)."""
    if field not in _BILL_RULES:
        raise KeyError(f"unknown bill field {field!r}")
    return bool(_BILL_RULES[field](got, expected))


RULES_TEXT = (
    "Text is Unicode-normalized, case-folded and whitespace-collapsed before comparing. Money must match to the cent. "
    "Dates must be the same calendar day after parsing. Hospital names and addresses match if equal after normalization "
    f"or if the fuzzy ratio (token sort) is ≥ {NAME_FUZZY_THRESHOLD:.2f}. Account numbers: case and whitespace ignored, "
    "separators kept. % of the poverty line must match exactly."
)
