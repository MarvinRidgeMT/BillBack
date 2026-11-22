"""Post-validation: verify quotes against page text, sanity-check numbers, set review flags.

Pure functions: inputs are never mutated; a new PolicyRules is returned.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Optional

from rapidfuzz import fuzz

from .schema import EVIDENCE_FIELDS, PolicyRules

QUOTE_MATCH_THRESHOLD = 90
UNVERIFIED_CONFIDENCE_CAP = 0.5
SANITY_CONFIDENCE_CAP = 0.6
REVIEW_CONFIDENCE_THRESHOLD = 0.8
MIN_QUOTE_CHARS = 12
FPL_PERCENT_RANGE = (100, 1000)
WINDOW_DAYS_RANGE = (30, 730)

_QUOTE_CHARS = {"‘": "'", "’": "'", "“": '"', "”": '"', " ": " "}
_DASHES = re.compile(r"[‐-―−-]")


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    for src, dst in _QUOTE_CHARS.items():
        text = text.replace(src, dst)
    text = _DASHES.sub("-", text)
    text = re.sub(r"-\s*\n\s*", "", text)  # hyphenated line break: "assis-\ntance"
    text = text.replace("-", "")  # "post-discharge" == "postdischarge"
    text = text.replace("|", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip().lower()


def _matches(quote_n: str, page_text: str) -> bool:
    page_n = normalize(page_text)
    if quote_n in page_n:
        return True
    return fuzz.partial_ratio(quote_n, page_n) >= QUOTE_MATCH_THRESHOLD


def find_quote(quote: str, pages: dict[int, str], page_hint: Optional[int]) -> tuple[bool, Optional[int]]:
    """Return (verified, page_where_found). Checks the hinted page first, then all others."""
    quote_n = normalize(quote)
    if len(quote_n) < MIN_QUOTE_CHARS:
        return False, page_hint
    order = ([page_hint] if page_hint in pages else []) + [n for n in pages if n != page_hint]
    for number in order:
        if _matches(quote_n, pages[number]):
            return True, number
    return False, page_hint


def _pct_in_range(value: Optional[float]) -> bool:
    return value is None or FPL_PERCENT_RANGE[0] <= value <= FPL_PERCENT_RANGE[1]


def sanity_problems(rules: PolicyRules) -> list[tuple[str, str]]:
    """(field, message) pairs for values that look wrong. Thresholds only — no eligibility math."""
    problems: list[tuple[str, str]] = []
    free = rules.free_care.fpl_max_percent
    disc = rules.discount.fpl_max_percent

    if not _pct_in_range(free):
        problems.append(("free_care", f"free_care.fpl_max_percent={free} is out of range {FPL_PERCENT_RANGE}"))
    if not _pct_in_range(disc):
        problems.append(("discount", f"discount.fpl_max_percent={disc} is out of range {FPL_PERCENT_RANGE}"))
    if free is not None and disc is not None and free > disc:
        problems.append(("free_care", f"free_care limit {free}% is above discount limit {disc}%"))

    tiers = rules.discount.tiers
    for i, tier in enumerate(tiers):
        lo, hi = tier.fpl_min_percent, tier.fpl_max_percent
        if lo is not None and hi is not None and lo > hi:
            problems.append(("discount", f"discount tier {i + 1} has min {lo}% above max {hi}%"))
        if not (_pct_in_range(hi) and (lo is None or lo == 0 or _pct_in_range(lo))):
            problems.append(("discount", f"discount tier {i + 1} percent out of range"))
    for i in range(1, len(tiers)):
        prev_hi, cur_lo = tiers[i - 1].fpl_max_percent, tiers[i].fpl_min_percent
        if prev_hi is not None and cur_lo is not None and cur_lo < prev_hi:
            problems.append(("discount", f"discount tiers {i} and {i + 1} overlap or are out of order"))

    days = rules.application_window.days
    if days is not None and not (WINDOW_DAYS_RANGE[0] <= days <= WINDOW_DAYS_RANGE[1]):
        problems.append(("application_window", f"application_window.days={days} outside {WINDOW_DAYS_RANGE}"))
    return problems


def _is_not_stated(field) -> bool:
    values = field.model_dump(exclude={"evidence"})
    return not field.evidence.quote.strip() and all(v in (None, [], "") for v in values.values())


def post_validate(rules: PolicyRules, pages: dict[int, str]) -> PolicyRules:
    data = rules.model_dump()
    warnings = list(data["warnings"])

    for name in EVIDENCE_FIELDS:
        field = getattr(rules, name)
        ev = data[name]["evidence"]
        if _is_not_stated(field):
            ev["verified"] = None
            continue
        verified, page = find_quote(ev["quote"], pages, ev["page"])
        ev["verified"] = verified
        if verified and page != ev["page"]:
            warnings.append(f"{name}: quote found on page {page}, not page {ev['page']}; page corrected")
            ev["page"] = page
        if not verified:
            ev["confidence"] = min(ev["confidence"], UNVERIFIED_CONFIDENCE_CAP)
            warnings.append(f"{name}: quote could not be found in the policy text")

    for name, message in sanity_problems(rules):
        data[name]["evidence"]["confidence"] = min(data[name]["evidence"]["confidence"], SANITY_CONFIDENCE_CAP)
        warnings.append(message)

    review = [
        name
        for name in EVIDENCE_FIELDS
        if data[name]["evidence"]["confidence"] < REVIEW_CONFIDENCE_THRESHOLD
        or data[name]["evidence"]["verified"] is False
    ]
    data["warnings"] = list(dict.fromkeys(warnings))
    data["review_fields"] = review
    data["needs_human_review"] = bool(review) or (rules.uses_income_table and rules.free_care.fpl_max_percent is None)
    return PolicyRules.model_validate(data)
