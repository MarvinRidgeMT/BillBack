"""Read-only facts from a cached policy for the result screen: thresholds (what-if slider), deadline,
presumptive eligibility and the hospital's state. Plain code from cached rules; no AI, no eligibility call.
"""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any, Optional

from backend import fpl, hospital_form, policies, policy_page
from backend.policy_reader.cache import REPO_ROOT
from backend.policy_reader.schema import PolicyRules

STATE_LAWS_PATH = REPO_ROOT / "data" / "state_laws.json"


@lru_cache(maxsize=1)
def _state_laws() -> dict[str, dict[str, Any]]:
    if not STATE_LAWS_PATH.exists():
        return {}
    return {row["state"]: row for row in json.loads(STATE_LAWS_PATH.read_text())["states"]}


def state_law(state: Optional[str]) -> Optional[dict[str, Any]]:
    """Information only: never used by the eligibility call."""
    return _state_laws().get(state.upper()) if state else None


def _tier_label(tier: Any) -> str:
    if tier.discount_type == "percent_off" and isinstance(tier.value, (int, float)):
        return f"{tier.value:g}% off"
    return {"sliding_scale": "sliding scale", "amount_generally_billed": "AGB discount"}.get(tier.discount_type, "discount")


def thresholds(slug: str, household_size: int, state: str) -> dict[str, Any]:
    """Zones to draw behind the slider. The status shown always comes from POST /api/eligibility."""
    rules, _ = policies.load_policy(slug)
    line = fpl.poverty_line(household_size, state)
    free_max = rules.free_care.fpl_max_percent
    tiers = [
        {
            "min_percent": t.fpl_min_percent,
            "max_percent": t.fpl_max_percent,
            "label": _tier_label(t),
            "discount_percent": t.value if t.discount_type == "percent_off" else None,
        }
        for t in rules.discount.tiers
        if t.fpl_max_percent is not None
    ]
    candidates = [free_max, rules.discount.fpl_max_percent, *(t["max_percent"] for t in tiers)]
    known = [c for c in candidates if isinstance(c, (int, float))]
    return {
        "poverty_line": line,
        "free_max_percent": free_max,
        "discount_max_percent": rules.discount.fpl_max_percent,
        "tiers": tiers,
        "max_percent": max(known) if known else None,
    }


def _evidence(ev: Any) -> dict[str, Any]:
    return {"quote": ev.quote, "page": ev.page, "status": ev.status}


def facts(slug: str) -> dict[str, Any]:
    rules, _ = policies.load_policy(slug)
    window = rules.application_window
    state = hospital_state(slug, rules)
    return {
        "hospital_name": rules.hospital_name,
        "hospital_state": state,
        "state_law": state_law(state),
        "application_window": {"days": window.days, "counted_from": window.counted_from, **_evidence(window.evidence)},
        "presumptive_eligibility": rules.presumptive_eligibility,
        "has_page_images": policy_page.pdf_path_for(slug) is not None,
        "own_form": hospital_form.form_for(slug, "en") is not None,
        "source_url": policies.source_url_for(rules),
    }


def hospital_state(slug: str, rules: Optional[PolicyRules] = None) -> Optional[str]:
    if rules is not None and rules.hospital_state:
        return rules.hospital_state
    for h in policies.load_index():
        if h["slug"] == slug:
            return h.get("state")
    return None
