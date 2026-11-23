"""Grounded view of the rules: every field with its value, the exact source sentence, page and confidence.

Derived from PolicyRules (the contract with B's engine stays unchanged). Plain code only:
- `verified` comes from validate.find_quote (the quote was found in the PDF text, normalized or fuzzy >= 90)
- `needs_checking` is True when the quote wasn't found, the policy is unclear, confidence < 0.8, or a sanity check failed
- `problems` lists why, in plain words, so the UI can say what to check
"""

from __future__ import annotations

from typing import Any

from .schema import EVIDENCE_FIELDS, PolicyRules
from .validate import REVIEW_CONFIDENCE_THRESHOLD, sanity_problems

PROBLEM_QUOTE_NOT_FOUND = "quote_not_found"
PROBLEM_UNCLEAR = "policy_unclear"
PROBLEM_LOW_CONFIDENCE = "low_confidence"
PROBLEM_NOT_STATED = "not_stated"
PROBLEM_SANITY = "failed_sanity_check"
NOT_STATED_OK = ("asset_test", "residency")  # silence here means "no restriction"


def field_value(rules: PolicyRules, name: str) -> Any:
    """The value a person would check against the policy, per field."""
    if name == "free_care":
        return rules.free_care.fpl_max_percent
    if name == "discount":
        return {
            "fpl_max_percent": rules.discount.fpl_max_percent,
            "tiers": [t.model_dump() for t in rules.discount.tiers],
        }
    if name == "asset_test":
        return {"applies": rules.asset_test.applies, "details": rules.asset_test.details}
    if name == "residency":
        return {"required": rules.residency.required, "area": rules.residency.area}
    if name == "application_window":
        return {"days": rules.application_window.days, "counted_from": rules.application_window.counted_from}
    raise KeyError(name)


def _problems(rules: PolicyRules, name: str, sanity: dict[str, list[str]]) -> list[str]:
    ev = getattr(rules, name).evidence
    out = []
    if ev.verified is False:
        out.append(PROBLEM_QUOTE_NOT_FOUND)
    if ev.status == "unclear":
        out.append(PROBLEM_UNCLEAR)
    if ev.status == "not_stated" and name not in NOT_STATED_OK:
        out.append(PROBLEM_NOT_STATED)
    if ev.status != "not_stated" and ev.confidence < REVIEW_CONFIDENCE_THRESHOLD:
        out.append(PROBLEM_LOW_CONFIDENCE)
    if sanity.get(name):
        out.append(PROBLEM_SANITY)
    return out


def grounded_view(rules: PolicyRules) -> dict[str, dict[str, Any]]:
    sanity: dict[str, list[str]] = {}
    for field, message in sanity_problems(rules):
        sanity.setdefault(field, []).append(message)
    view = {}
    for name in EVIDENCE_FIELDS:
        ev = getattr(rules, name).evidence
        problems = _problems(rules, name, sanity)
        view[name] = {
            "value": field_value(rules, name),
            "source_quote": ev.quote,
            "page": ev.page,
            "confidence": ev.confidence,
            "status": ev.status,
            "verified": ev.verified,
            "needs_checking": bool(problems) or name in rules.review_fields,
            "problems": problems,
            "sanity_messages": sanity.get(name, []),
        }
    return view


def needs_checking(rules: PolicyRules) -> list[str]:
    return [name for name, f in grounded_view(rules).items() if f["needs_checking"]]
