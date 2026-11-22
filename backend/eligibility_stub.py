"""STUB — B replaces this with the real rules engine (plain Python + pytest).

Takes a household's percent of FPL plus a cached policy (rules JSON) and returns a likely
result and the policy quote it relied on. No AI here. Thresholds come from the policy reader.
"""

from __future__ import annotations

import csv
import hashlib
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

from backend.policy_reader.cache import DEFAULT_CACHE_DIR, REPO_ROOT
from backend.policy_reader.schema import DiscountTier, PolicyRules

DISCLAIMER = "Likely eligible — not a guarantee"
SOURCES_CSV = REPO_ROOT / "data" / "policies" / "sources.csv"
_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,59}$")


def load_policy(slug: str, cache_dir: Path = DEFAULT_CACHE_DIR) -> tuple[PolicyRules, Path]:
    """Load cache/policies/<slug>__<sha8>.json. The slug is validated so it can't escape the folder."""
    if not isinstance(slug, str) or not _SLUG_RE.match(slug):
        raise ValueError("hospital_slug must be lowercase letters, digits and dashes")
    matches = sorted(Path(cache_dir).glob(f"{slug}__*.json"))
    if not matches:
        raise LookupError(f"no cached policy for '{slug}'")
    return PolicyRules.model_validate_json(matches[0].read_text()), matches[0]


@lru_cache(maxsize=1)
def _sha_to_url() -> dict[str, str]:
    if not SOURCES_CSV.exists():
        return {}
    out = {}
    with SOURCES_CSV.open() as fh:
        for row in csv.DictReader(fh):
            pdf = SOURCES_CSV.parent / row["file"]
            if pdf.exists():
                out[hashlib.sha256(pdf.read_bytes()).hexdigest()] = row["url"]
    return out


def source_url(rules: PolicyRules) -> Optional[str]:
    if rules.source is None:
        return None
    return rules.source.url or _sha_to_url().get(rules.source.sha256)


def _matching_tier(pct: float, tiers: list[DiscountTier]) -> Optional[DiscountTier]:
    # First tier whose upper bound covers pct; a gap like 200.5 between "<=200" and "201-300" lands in 201-300.
    for tier in tiers:
        if tier.fpl_max_percent is None or pct <= tier.fpl_max_percent:
            return tier
    return None


def _caveats(rules: PolicyRules) -> list[str]:
    notes = []
    if rules.residency.required:
        notes.append(f"Residency required: {rules.residency.area or 'see policy'}")
    if rules.asset_test.applies:
        notes.append(f"Assets may be considered: {rules.asset_test.details or 'see policy'}")
    if rules.needs_human_review:
        notes.append("Some policy details need confirming: " + ", ".join(rules.review_fields))
    return notes


def decide(pct: float, rules: PolicyRules) -> dict[str, Any]:
    free_max = rules.free_care.fpl_max_percent
    disc_max = rules.discount.fpl_max_percent
    result: dict[str, Any] = {"tier": None, "caveats": _caveats(rules), "disclaimer": DISCLAIMER}

    if free_max is not None and pct <= free_max:
        return {**result, "status": "likely_free", "evidence": rules.free_care.evidence.model_dump()}
    upper = disc_max if disc_max is not None else max((t.fpl_max_percent or 0 for t in rules.discount.tiers), default=None)
    if upper and pct <= upper:
        tier = _matching_tier(pct, rules.discount.tiers)
        return {
            **result,
            "status": "likely_discounted",
            "tier": tier.model_dump() if tier else None,
            "evidence": rules.discount.evidence.model_dump(),
        }
    if free_max is None and upper is None:
        return {**result, "status": "cannot_determine", "evidence": rules.free_care.evidence.model_dump()}
    return {**result, "status": "probably_not_eligible", "evidence": rules.discount.evidence.model_dump()}
