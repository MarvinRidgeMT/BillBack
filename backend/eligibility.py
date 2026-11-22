"""Bridge: maps Person A's PolicyRules → Person B's EligibilityEngine.

This module replaces eligibility_stub.decide() with the real rules engine.
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


def _build_conditions_from_rules(rules: PolicyRules) -> list[PolicyCondition]:
    """Build common conditions from PolicyRules that apply across tiers."""
    conditions = []

    # Residency condition - use hospital_state (2-letter code) as verified_value for matching
    if rules.residency.required is not None:
        conditions.append(
            PolicyCondition(
                name="residency",
                description=f"Residency required: {rules.residency.area or rules.hospital_state or 'policy area'}",
                required=True,
                verified_value=rules.hospital_state,  # Use 2-letter state code for matching against household.residency_state
                evidence_ref=rules.residency.evidence.quote[:100] if rules.residency.evidence.quote else None,
            )
        )

    # Asset test condition - only add if applies=True
    if rules.asset_test.applies is True:
        conditions.append(
            PolicyCondition(
                name="asset_test",
                description=rules.asset_test.details or "Asset test applies",
                required=True,
                evidence_ref=rules.asset_test.evidence.quote[:100] if rules.asset_test.evidence.quote else None,
            )
        )

    # Application window (informational, not a condition that blocks eligibility)
    # Skip adding as a condition - it's informational only
    # if rules.application_window.days is not None:
    #     conditions.append(...)

    return conditions


def policy_rules_to_hospital_policy(rules: PolicyRules) -> HospitalPolicy:
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
            evidence_ref=rules.free_care.evidence.quote[:200] if rules.free_care.evidence.quote else None,
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
            evidence_ref=rules.discount.evidence.quote[:200] if rules.discount.evidence.quote else None,
            priority=i + 1,  # Free care is priority 0, then discount tiers
        )
        tiers.append(discount_tier)

    # If no free_care but has discount, add a catch-all "probably not eligible" indicator
    # (The engine handles this via status NEEDS_MORE_INFORMATION -> PROBABLY_NOT_ELIGIBLE)

    # Determine default FPL year and region
    default_fpl_year = 2024  # Synthetic test data uses 2024 guidelines; production uses data/fpl_2026.json
    default_region = "contiguous"  # Most states use contiguous

    # Map hospital_state to region
    if rules.hospital_state:
        state = rules.hospital_state.upper()
        if state == "AK":
            default_region = "alaska"
        elif state == "HI":
            default_region = "hawaii"

    return HospitalPolicy(
        policy_id=f"{rules.hospital_name.lower().replace(' ', '-')}-{rules.policy_effective_date or 'unknown'}",
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
            for hs in range(9, 21):
                amount = Decimal(str(base_8)) + Decimal(str(additional)) * (hs - 8)
                resolver.add_guideline(FPLGuideline(year, region, hs, amount))

    return resolver


def run_eligibility(
    rules: PolicyRules,
    household_size: int,
    annual_income: float,
    state: str,
    fpl_resolver: Optional[PovertyGuidelineResolver] = None,
    assets_usd: Optional[float] = None,
    insurance_status: Optional[str] = None,
    residency_state: Optional[str] = None,
) -> EligibilityResult:
    """Run the real eligibility engine with Person A's PolicyRules."""
    policy = policy_rules_to_hospital_policy(rules)
    household = build_household_facts(
        household_size=household_size,
        annual_income=annual_income,
        state=state,
        assets_usd=assets_usd,
        insurance_status=insurance_status,
        residency_state=residency_state,
    )

    # Use provided resolver or create synthetic one for testing
    if fpl_resolver is None:
        fpl_resolver = PovertyGuidelineResolver()  # Will use synthetic defaults if empty

    return evaluate_eligibility(policy, household, fpl_resolver)


def eligibility_result_to_api_response(result: EligibilityResult, rules: PolicyRules, percent_of_fpl: float) -> dict[str, Any]:
    """Convert EligibilityResult to the API response format expected by frontend."""
    status_map = {
        EligibilityStatus.LIKELY_FREE: "likely_free",
        EligibilityStatus.LIKELY_DISCOUNTED: "likely_discounted",
        EligibilityStatus.PROBABLY_NOT_ELIGIBLE: "probably_not_eligible",
        EligibilityStatus.NEEDS_MORE_INFORMATION: "needs_more_information",
    }

    api_status = status_map.get(result.status, "needs_more_information")

    # Build caveats (similar to stub)
    caveats = []
    if rules.residency.required:
        caveats.append(f"Residency required: {rules.residency.area or 'see policy'}")
    if rules.asset_test.applies:
        caveats.append(f"Assets may be considered: {rules.asset_test.details or 'see policy'}")
    if rules.needs_human_review:
        caveats.append("Some policy details need confirming: " + ", ".join(rules.review_fields))

    # Determine tier info
    tier_info = None
    evidence = None

    if result.matching_tier:
        tier_info = {
            "tier_id": result.matching_tier.tier_id,
            "name": result.matching_tier.name,
            "type": result.matching_tier.type,
            "threshold_value": str(result.matching_tier.threshold_value),
            "threshold_type": result.matching_tier.threshold_type.value,
            "inclusivity": result.matching_tier.inclusivity.value,
            "discount_percent": str(result.matching_tier.discount_percent) if result.matching_tier.discount_percent else None,
            "discount_formula": result.matching_tier.discount_formula,
        }

        # Use the matching tier's evidence
        if result.matching_tier.type == "free":
            evidence = rules.free_care.evidence.model_dump()
        else:
            evidence = rules.discount.evidence.model_dump()
    else:
        # No matching tier - use discount evidence or free care evidence
        evidence = rules.discount.evidence.model_dump() if rules.discount.tiers else rules.free_care.evidence.model_dump()

    return {
        "status": api_status,
        "tier": tier_info,
        "caveats": caveats,
        "disclaimer": "Likely eligible — not a guarantee",
        "evidence": evidence,
        "percent_of_fpl": round(percent_of_fpl, 2),
        "hospital_name": rules.hospital_name,
        "source_url": rules.source.url if rules.source else None,
        "engine": "rules",
        # Extended fields from real engine
        "explanation": result.explanation,
        "missing_facts": result.missing_facts,
        "unresolved_rules": result.unresolved_rules,
        "policy_id": result.policy_id,
        "fpl_used": result.fpl_used,
        "fpl_year": result.fpl_year,
        "fpl_region": result.fpl_region,
    }