"""Bridge: maps Person A's PolicyRules → Person B's EligibilityEngine (billback/eligibility.py).

Written by B, integrated by A. No AI here: thresholds come from the policy reader, the decision from B's engine.
- not_stated residency/asset -> no condition; unclear or < 0.8 confidence -> an unresolved condition (never a pass)
- FPL comes from data/fpl_2026.json; the year and region (from the household's state) are passed explicitly
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Optional

from backend.policy_reader.schema import PolicyRules

from billback.eligibility import (
    EligibilityEngine,
    HospitalPolicy,
    HouseholdFacts,
    AssistanceTier,
    PolicyCondition,
    EligibilityResult,
    EligibilityStatus,
    ConditionState,
    ThresholdType,
    Inclusivity,
    PovertyGuidelineResolver,
    FPLGuideline,
    evaluate_eligibility,
)


def _map_inclusivity(inclusivity_str: str | None) -> Inclusivity:
    """Map inclusivity string to enum. Default to inclusive if not specified."""
    if not inclusivity_str:
        return Inclusivity.INCLUSIVE
    lower = inclusivity_str.lower()
    if "exclusive" in lower or "<" in lower and "=" not in lower:
        return Inclusivity.EXCLUSIVE
    return Inclusivity.INCLUSIVE


def _map_threshold_type(income_basis: str | None, uses_income_table: bool) -> ThresholdType:
    """Map income_basis to threshold type."""
    if uses_income_table or (income_basis and "table" in income_basis.lower()):
        return ThresholdType.FIXED_INCOME_TABLE
    return ThresholdType.FPL_PERCENTAGE


REVIEW_CONFIDENCE = 0.8
MAX_HOUSEHOLD = 30  # matches the API's household_size limit
DISCLAIMER = "Likely eligible, not a guarantee."
# Names deliberately avoid the engine's "residen"/"asset" keywords so they always evaluate as UNKNOWN.
_UNRESOLVED_NAMES = {"residency": "unresolved_home_area_rule", "asset_test": "unresolved_savings_rule"}
PLAIN_FIELD_NAMES = {
    "free_care": "the free-care income limit",
    "discount": "the discount income limits",
    "asset_test": "whether savings or property count",
    "residency": "where you need to live",
    "application_window": "how long you have to apply",
}


def _unresolved(field: str, rules: PolicyRules) -> bool:
    ev = getattr(rules, field).evidence
    return ev.status == "unclear" or ev.confidence < REVIEW_CONFIDENCE or ev.verified is False


def _quote_ref(ev) -> Optional[str]:
    if not ev.quote:
        return None
    return f"Page {ev.page}: {ev.quote[:200]}" if ev.page else ev.quote[:200]


def _build_conditions_from_rules(rules: PolicyRules) -> list[PolicyCondition]:
    """Residency and asset conditions that apply to every tier."""
    conditions = []
    for field in ("residency", "asset_test"):
        part = getattr(rules, field)
        ev = part.evidence
        if ev.status == "not_stated":
            continue  # policy is silent -> no restriction (UI tells the patient the policy doesn't say)
        if _unresolved(field, rules):
            conditions.append(
                PolicyCondition(
                    name=_UNRESOLVED_NAMES[field],
                    description=f"Policy is unclear about {PLAIN_FIELD_NAMES[field]}; a person needs to check",
                    required=True,
                    evidence_ref=_quote_ref(ev),
                )
            )
            continue
        if field == "residency" and rules.residency.required:
            conditions.append(
                PolicyCondition(
                    name="residency",
                    description=f"Residency required: {rules.residency.area or rules.hospital_state or 'policy area'}",
                    required=True,
                    verified_value=rules.hospital_state,  # household state must match (approximation of service area)
                    evidence_ref=_quote_ref(ev),
                )
            )
        if field == "asset_test" and rules.asset_test.applies:
            conditions.append(
                PolicyCondition(
                    name="asset_test",
                    description=rules.asset_test.details or "Asset test applies",
                    required=True,
                    evidence_ref=_quote_ref(ev),
                )
            )
    return conditions


def policy_rules_to_hospital_policy(rules: PolicyRules, fpl_year: int = 2026) -> HospitalPolicy:
    """Convert Person A's PolicyRules to Person B's HospitalPolicy."""
    tiers: list[AssistanceTier] = []
    common_conditions = _build_conditions_from_rules(rules)

    # Free care tier
    if rules.free_care.fpl_max_percent is not None:
        free_tier = AssistanceTier(
            tier_id="free",
            name="Free Care",
            type="free",
            threshold_type=ThresholdType.FPL_PERCENTAGE,
            threshold_value=Decimal(str(rules.free_care.fpl_max_percent)),
            inclusivity=Inclusivity.INCLUSIVE,  # "at or below" per policy convention
            discount_percent=None,
            discount_formula=None,
            conditions=common_conditions.copy(),
            scope={},
            evidence_ref=_quote_ref(rules.free_care.evidence),
            priority=0,
        )
        tiers.append(free_tier)

    # Discount tiers
    for i, tier_data in enumerate(rules.discount.tiers):
        discount_type = tier_data.discount_type
        discount_percent = None
        discount_formula = None

        if discount_type == "percent_off" and tier_data.value is not None:
            discount_percent = Decimal(str(tier_data.value))
        elif discount_type == "pays_percent_of_charges" and tier_data.value is not None:
            discount_formula = f"Patient pays {tier_data.value}% of charges"
        elif discount_type == "amount_generally_billed":
            discount_formula = "Amount Generally Billed (AGB)"
        elif discount_type == "sliding_scale":
            discount_formula = "Sliding scale"
        elif discount_type == "other":
            discount_formula = tier_data.description or "Other discount"

        # Determine threshold values
        fpl_min = tier_data.fpl_min_percent
        fpl_max = tier_data.fpl_max_percent
        if fpl_max is None:
            continue  # open-ended band ("> 400%: varies by facility") has no income limit to test

        # For discount tiers, use fpl_max_percent as the threshold with inclusive boundary
        # The tier covers fpl_min to fpl_max
        threshold_value = Decimal(str(fpl_max)) if fpl_max is not None else Decimal("0")

        # Inclusivity: for discount tiers, the upper bound is typically inclusive
        inclusivity = Inclusivity.INCLUSIVE

        discount_tier = AssistanceTier(
            tier_id=f"discount-{i}",
            name=tier_data.description or f"Discount Tier {i+1}",
            type="discounted",
            threshold_type=ThresholdType.FPL_PERCENTAGE,
            threshold_value=threshold_value,
            inclusivity=inclusivity,
            discount_percent=discount_percent,
            discount_formula=discount_formula,
            conditions=common_conditions.copy(),
            scope={"fpl_min_percent": fpl_min} if fpl_min is not None else {},
            evidence_ref=_quote_ref(rules.discount.evidence),
            priority=i + 1,  # Free care is priority 0, then discount tiers
        )
        tiers.append(discount_tier)

    # If no free_care but has discount, add a catch-all "probably not eligible" indicator
    # (The engine handles this via status NEEDS_MORE_INFORMATION -> PROBABLY_NOT_ELIGIBLE)

    # Determine default FPL year and region
    default_fpl_year = fpl_year  # the year of the table actually loaded (data/fpl_2026.json -> 2026)
    default_region = "contiguous"  # Most states use contiguous

    # Map hospital_state to region
    if rules.hospital_state:
        state = rules.hospital_state.upper()
        if state == "AK":
            default_region = "alaska"
        elif state == "HI":
            default_region = "hawaii"

    return HospitalPolicy(
        policy_id=f"{rules.hospital_name.lower().replace(' ', '-')}",
        hospital_name=rules.hospital_name,
        facility_names=[],  # Not in PolicyRules
        state=rules.hospital_state or "XX",
        source_url=rules.source.url if rules.source else "",
        retrieval_date=rules.source.retrieved_at if rules.source else "",
        effective_date=rules.policy_effective_date,
        version=None,
        tiers=tiers,
        default_fpl_year=default_fpl_year,
        default_region=default_region,
    )


def build_household_facts(
    household_size: int,
    annual_income: float,
    state: str,
    assets_usd: Optional[float] = None,
    insurance_status: Optional[str] = None,
    residency_state: Optional[str] = None,
) -> HouseholdFacts:
    """Build HouseholdFacts from API request parameters."""
    return HouseholdFacts(
        household_size=household_size,
        annual_income_usd=Decimal(str(annual_income)),
        residency_state=residency_state or state,
        residency_county=None,
        assets_usd=Decimal(str(assets_usd)) if assets_usd is not None else None,
        insurance_status=insurance_status,
        facility_name=None,
        service_type=None,
        patient_age=None,
        patient_citizenship=None,
        extra={},
    )


def load_fpl_table_from_json(path_or_data: str | dict) -> PovertyGuidelineResolver:
    """Load FPL guidelines from JSON file or dict into a PovertyGuidelineResolver.

    Expected JSON format (matching backend/fpl.py DEFAULT_TABLE_PATH):
    {
      "year": 2026,
      "tables": {
        "contiguous": {"base": {"1": 15060, "2": 20440, ...}, "additional_person": 5380},
        "AK": {"base": {...}, "additional_person": ...},
        "HI": {"base": {...}, "additional_person": ...}
      }
    }
    """
    import json
    from pathlib import Path

    if isinstance(path_or_data, dict):
        data = path_or_data
    else:
        data = json.loads(Path(path_or_data).read_text())

    tables = data.get("tables", {})
    resolver = PovertyGuidelineResolver()

    year = data.get("year", 2026)

    for region_key, table in tables.items():
        base = table.get("base", {})
        additional = table.get("additional_person", 0)
        region = region_key.lower()
        if region == "ak":
            region = "alaska"
        elif region == "hi":
            region = "hawaii"

        # Add base household sizes (1-8)
        for hs_str, amount in base.items():
            hs = int(hs_str)
            resolver.add_guideline(FPLGuideline(year, region, hs, Decimal(str(amount))))

        # Add larger household sizes using additional_person increment
        if additional > 0:
            base_8 = base.get("8", 0)
            for hs in range(9, MAX_HOUSEHOLD + 1):
                amount = Decimal(str(base_8)) + Decimal(str(additional)) * (hs - 8)
                resolver.add_guideline(FPLGuideline(year, region, hs, amount))

    return resolver


def fpl_region_for_state(state: str) -> str:
    code = state.strip().upper()
    return {"AK": "alaska", "HI": "hawaii"}.get(code, "contiguous")


def run_eligibility(
    rules: PolicyRules,
    household_size: int,
    annual_income: float,
    state: str,
    fpl_resolver: PovertyGuidelineResolver,
    fpl_year: int,
    assets_usd: Optional[float] = None,
    insurance_status: Optional[str] = None,
    residency_state: Optional[str] = None,
) -> EligibilityResult:
    """Run B's engine. FPL year = the loaded table's year; region = the household's state (AK/HI rows)."""
    policy = policy_rules_to_hospital_policy(rules, fpl_year=fpl_year)
    household = build_household_facts(
        household_size=household_size,
        annual_income=annual_income,
        state=state,
        assets_usd=assets_usd,
        insurance_status=insurance_status,
        residency_state=residency_state,
    )
    return evaluate_eligibility(policy, household, fpl_resolver, fpl_year=fpl_year, fpl_region=fpl_region_for_state(state))


_STATUS_MAP = {
    EligibilityStatus.LIKELY_FREE: "likely_free",
    EligibilityStatus.LIKELY_DISCOUNTED: "likely_discounted",
    EligibilityStatus.PROBABLY_NOT_ELIGIBLE: "probably_not_eligible",
    EligibilityStatus.NEEDS_MORE_INFORMATION: "cannot_determine",  # the UI's word for it
}
_MISSING_FACT_WORDS = {
    "asset_test": "how much you have in savings or property",
    "residency": "which state you live in",
    "unresolved_home_area_rule": "the policy's home-area rule (unclear in the policy)",
    "unresolved_savings_rule": "the policy's savings rule (unclear in the policy)",
}


def _plain_missing(fact: str) -> str:
    for key, words in _MISSING_FACT_WORDS.items():
        if key in fact:
            return words
    return fact.replace("_", " ")


def _caveats(rules: PolicyRules, result: EligibilityResult) -> list[str]:
    notes = []
    if rules.residency.evidence.status != "not_stated" and rules.residency.required:
        notes.append(f"You may need to live in: {rules.residency.area or 'the hospital area'}.")
    if rules.asset_test.evidence.status != "not_stated" and rules.asset_test.applies:
        notes.append(f"Savings or property may count: {rules.asset_test.details or 'see the policy'}.")
    for field in ("residency", "asset_test"):
        if getattr(rules, field).evidence.status == "not_stated":
            notes.append(f"The policy doesn't say anything about {PLAIN_FIELD_NAMES[field]}.")
    review = [PLAIN_FIELD_NAMES.get(f, f) for f in rules.review_fields]
    if review:
        notes.append("Please double-check with the hospital: " + ", ".join(review) + ".")
    missing = sorted({_plain_missing(m) for m in result.missing_facts})
    if missing:
        notes.append("We still need to know: " + "; ".join(missing) + ".")
    return notes


def _matched_rules_tier(result: EligibilityResult, rules: PolicyRules) -> Optional[dict[str, Any]]:
    """The policy's own tier dict (C's UI shape) for the engine's matching discount tier."""
    tier = result.matching_tier
    if tier is None or tier.type == "free" or not tier.tier_id.startswith("discount-"):
        return None
    index = int(tier.tier_id.split("-", 1)[1])
    return rules.discount.tiers[index].model_dump() if index < len(rules.discount.tiers) else None


def eligibility_result_to_api_response(
    result: EligibilityResult, rules: PolicyRules, percent_of_fpl: float, source_url: Optional[str]
) -> dict[str, Any]:
    """Shape the engine result for the UI (frontend/lib/types.ts EligibilityData) plus engine details."""
    status = _STATUS_MAP.get(result.status, "cannot_determine")
    explanation = result.explanation
    if rules.uses_income_table and rules.free_care.fpl_max_percent is None and not rules.discount.tiers:
        status = "cannot_determine"
        explanation = "This policy lists income limits as a dollar table, not a percent of the poverty level, so we can't check it automatically."

    if result.matching_tier is not None and result.matching_tier.type == "free":
        evidence_field = rules.free_care.evidence
    elif result.matching_tier is not None or rules.discount.tiers:
        evidence_field = rules.discount.evidence
    else:
        evidence_field = rules.free_care.evidence
    evidence = {**evidence_field.model_dump(), "source_url": source_url}

    engine_tier = None
    if result.matching_tier:
        t = result.matching_tier
        engine_tier = {
            "tier_id": t.tier_id,
            "name": t.name,
            "type": t.type,
            "threshold_value": str(t.threshold_value),
            "inclusivity": t.inclusivity.value,
            "discount_percent": str(t.discount_percent) if t.discount_percent is not None else None,
            "discount_formula": t.discount_formula,
        }

    return {
        "status": status,
        "tier": _matched_rules_tier(result, rules),
        "evidence": evidence,
        "caveats": _caveats(rules, result),
        "disclaimer": DISCLAIMER,
        "percent_of_fpl": round(percent_of_fpl, 2),
        "hospital_name": rules.hospital_name,
        "source_url": source_url,
        "engine": "rules",
        "explanation": explanation,
        "missing_facts": result.missing_facts,
        "unresolved_rules": result.unresolved_rules,
        "engine_tier": engine_tier,
        "policy_id": result.policy_id,
        "fpl_used": str(result.fpl_used) if result.fpl_used is not None else None,
        "fpl_year": result.fpl_year,
        "fpl_region": result.fpl_region,
        "fpl_evidence": next((e for e in result.evidence if e.get("type") == "fpl_reference"), None),
    }
