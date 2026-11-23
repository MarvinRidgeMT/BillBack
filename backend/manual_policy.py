"""Rules from limits the patient typed in (live mode's last resort when a policy can't be fetched or read).

No AI. The patient copies two numbers from the hospital's policy; everything else is "not stated" and the
application window is flagged for checking. Kept in memory only (backend/live_session.py).
"""

from __future__ import annotations

import hashlib
from datetime import date
from typing import Optional

from backend import live_session
from backend.policy_reader.schema import (
    ApplicationWindow,
    AssetTest,
    Discount,
    DiscountTier,
    Evidence,
    FreeCare,
    PolicyRules,
    Residency,
    Source,
)

ENTERED_BY_PATIENT = "Entered by the patient from the hospital's policy."
NOT_STATED = Evidence(quote="", page=None, confidence=0.9, status="not_stated")


def _typed(confidence: float = 0.9) -> Evidence:
    # verified=None: there is no document to check a quote against; the patient is the source.
    return Evidence(quote=ENTERED_BY_PATIENT, page=None, confidence=confidence, status="stated", verified=None)


def build(hospital_name: str, state: str, free_max: float, discount_max: Optional[float]) -> PolicyRules:
    key = f"{hospital_name.strip().lower()}|{state.upper()}|{free_max}|{discount_max}"
    sha = hashlib.sha256(key.encode("utf-8")).hexdigest()
    tiers = []
    if discount_max is not None and discount_max > free_max:
        tiers = [DiscountTier(fpl_min_percent=free_max, fpl_max_percent=discount_max, discount_type="other",
                              value=None, description="Discount amount not entered; the hospital will tell you")]
    return PolicyRules(
        hospital_name=hospital_name.strip(),
        hospital_state=state.upper(),
        source=Source(url=None, sha256=sha, retrieved_at=date.today().isoformat(), page_count=0),
        free_care=FreeCare(fpl_max_percent=free_max, evidence=_typed()),
        discount=Discount(fpl_max_percent=discount_max, tiers=tiers,
                          evidence=_typed() if discount_max is not None else NOT_STATED),
        asset_test=AssetTest(evidence=NOT_STATED),
        residency=Residency(evidence=NOT_STATED),
        application_window=ApplicationWindow(evidence=Evidence(status="not_stated", confidence=0.9)),
        income_basis="fpl_percent",
        needs_human_review=True,
        review_fields=["application_window"],
        warnings=["Limits were typed in by the patient; savings and residency rules were not checked."],
    )


def slug_for(rules: PolicyRules) -> str:
    assert rules.source is not None
    return f"{live_session.PREFIX}manual-{rules.source.sha256[:8]}"
