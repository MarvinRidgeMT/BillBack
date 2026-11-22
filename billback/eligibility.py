"""
BillBack Eligibility Engine

Deterministic Python rules engine for hospital financial assistance screening.
Independent of FastAPI and AI policy reader.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Any, Optional
import json


class EligibilityStatus(str, Enum):
    """Final screening status values."""
    LIKELY_FREE = "likely_free"
    LIKELY_DISCOUNTED = "likely_discounted"
    PROBABLY_NOT_ELIGIBLE = "probably_not_eligible"
    NEEDS_MORE_INFORMATION = "needs_more_information"


class ConditionState(str, Enum):
    """State of a policy condition."""
    SATISFIED = "satisfied"
    NOT_SATISFIED = "not_satisfied"
    UNKNOWN = "unknown"
    NOT_APPLICABLE = "not_applicable"


class ThresholdType(str, Enum):
    """Type of income threshold."""
    FPL_PERCENTAGE = "fpl_percentage"
    FIXED_INCOME_TABLE = "fixed_income_table"


class Inclusivity(str, Enum):
    """Whether threshold boundary is inclusive."""
    INCLUSIVE = "inclusive"      # "at or below" / "<="
    EXCLUSIVE = "exclusive"      # "below" / "<"


@dataclass
class PolicyCondition:
    """A condition that must be met for a tier."""
    name: str
    description: str
    required: bool = True
    state: ConditionState = ConditionState.UNKNOWN
    verified_value: Any = None
    evidence_ref: Optional[str] = None


@dataclass
class AssistanceTier:
    """A single tier of financial assistance."""
    tier_id: str
    name: str
    type: str  # "free" or "discounted"
    threshold_type: ThresholdType
    threshold_value: Decimal  # FPL percentage (e.g., 200) or index into income table
    inclusivity: Inclusivity
    discount_percent: Optional[Decimal] = None  # For discounted care
    discount_formula: Optional[str] = None      # Human-readable formula
    conditions: list[PolicyCondition] = field(default_factory=list)
    scope: dict[str, Any] = field(default_factory=dict)  # facility, provider, service, patient
    evidence_ref: Optional[str] = None
    priority: int = 0  # Lower = higher priority


@dataclass
class HospitalPolicy:
    """Structured hospital financial assistance policy."""
    policy_id: str
    hospital_name: str
    facility_names: list[str]
    state: str
    source_url: str
    retrieval_date: str
    effective_date: Optional[str] = None
    version: Optional[str] = None
    tiers: list[AssistanceTier] = field(default_factory=list)
    default_fpl_year: int = 2024
    default_region: str = "contiguous"  # "contiguous", "alaska", "hawaii"


@dataclass
class HouseholdFacts:
    """Patient household information for screening."""
    household_size: int
    annual_income_usd: Decimal
    residency_state: Optional[str] = None
    residency_county: Optional[str] = None
    assets_usd: Optional[Decimal] = None
    insurance_status: Optional[str] = None  # "uninsured", "insured", "underinsured", "medicaid", "medicare"
    facility_name: Optional[str] = None
    service_type: Optional[str] = None  # "emergency", "inpatient", "outpatient", "elective"
    patient_age: Optional[int] = None
    patient_citizenship: Optional[str] = None  # "citizen", "legal_resident", "undocumented", "unknown"
    extra: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.household_size <= 0:
            raise ValueError("household_size must be a positive integer")
        if self.annual_income_usd < 0:
            raise ValueError("annual_income_usd must be nonnegative")


@dataclass
class FPLGuideline:
    """Federal Poverty Level guideline for a specific year/region/household size."""
    year: int
    region: str
    household_size: int
    annual_amount_usd: Decimal


@dataclass
class TierEvaluation:
    """Result of evaluating a single tier."""
    tier: AssistanceTier
    income_comparison: Optional[str] = None  # e.g., "income <= threshold"
    income_qualifies: Optional[bool] = None
    condition_results: list[tuple[PolicyCondition, ConditionState]] = field(default_factory=list)
    all_conditions_met: bool = False
    missing_conditions: list[str] = field(default_factory=list)
    failed_conditions: list[str] = field(default_factory=list)
    qualifies: bool = False


@dataclass
class EligibilityResult:
    """Final eligibility screening result."""
    status: EligibilityStatus
    explanation: str
    matching_tier: Optional[AssistanceTier] = None
    tier_evaluations: list[TierEvaluation] = field(default_factory=list)
    missing_facts: list[str] = field(default_factory=list)
    unresolved_rules: list[str] = field(default_factory=list)
    evidence: list[dict[str, Any]] = field(default_factory=list)
    policy_id: str = ""
    household_size: int = 0
    annual_income_usd: Decimal = Decimal("0")
    fpl_used: Optional[Decimal] = None
    fpl_year: Optional[int] = None
    fpl_region: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            "status": self.status.value,
            "explanation": self.explanation,
            "matching_tier": {
                "tier_id": self.matching_tier.tier_id,
                "name": self.matching_tier.name,
                "type": self.matching_tier.type,
            } if self.matching_tier else None,
            "tier_evaluations": [
                {
                    "tier_id": te.tier.tier_id,
                    "tier_name": te.tier.name,
                    "income_comparison": te.income_comparison,
                    "income_qualifies": te.income_qualifies,
                    "conditions": [
                        {"name": c.name, "state": s.value}
                        for c, s in te.condition_results
                    ],
                    "all_conditions_met": te.all_conditions_met,
                    "missing_conditions": te.missing_conditions,
                    "failed_conditions": te.failed_conditions,
                    "qualifies": te.qualifies,
                }
                for te in self.tier_evaluations
            ],
            "missing_facts": self.missing_facts,
            "unresolved_rules": self.unresolved_rules,
            "evidence": self.evidence,
            "policy_id": self.policy_id,
            "household_size": self.household_size,
            "annual_income_usd": str(self.annual_income_usd),
            "fpl_used": str(self.fpl_used) if self.fpl_used else None,
            "fpl_year": self.fpl_year,
            "fpl_region": self.fpl_region,
        }


class PovertyGuidelineResolver:
    """Resolves FPL values from a provided table or synthetic defaults."""

    def __init__(self, guidelines: list[FPLGuideline] | None = None):
        self._table: dict[tuple[int, str, int], Decimal] = {}
        if guidelines:
            for g in guidelines:
                self._table[(g.year, g.region.lower(), g.household_size)] = g.annual_amount_usd

    def get_fpl(self, year: int, region: str, household_size: int) -> Optional[Decimal]:
        """Get FPL amount for given parameters."""
        return self._table.get((year, region.lower(), household_size))

    def add_guideline(self, guideline: FPLGuideline) -> None:
        """Add a guideline to the table."""
        self._table[(guideline.year, guideline.region.lower(), guideline.household_size)] = guideline.annual_amount_usd


# Synthetic 2024 FPL guidelines for testing (contiguous 48 states)
SYNTHETIC_2024_FPL_CONTIGUOUS = [
    FPLGuideline(2024, "contiguous", 1, Decimal("15060")),
    FPLGuideline(2024, "contiguous", 2, Decimal("20440")),
    FPLGuideline(2024, "contiguous", 3, Decimal("25820")),
    FPLGuideline(2024, "contiguous", 4, Decimal("31200")),
    FPLGuideline(2024, "contiguous", 5, Decimal("36580")),
    FPLGuideline(2024, "contiguous", 6, Decimal("41960")),
    FPLGuideline(2024, "contiguous", 7, Decimal("47340")),
    FPLGuideline(2024, "contiguous", 8, Decimal("52720")),
]

SYNTHETIC_2024_FPL_ALASKA = [
    FPLGuideline(2024, "alaska", 1, Decimal("18810")),
    FPLGuideline(2024, "alaska", 2, Decimal("25540")),
    FPLGuideline(2024, "alaska", 3, Decimal("32270")),
    FPLGuideline(2024, "alaska", 4, Decimal("39000")),
    FPLGuideline(2024, "alaska", 5, Decimal("45730")),
    FPLGuideline(2024, "alaska", 6, Decimal("52460")),
    FPLGuideline(2024, "alaska", 7, Decimal("59190")),
    FPLGuideline(2024, "alaska", 8, Decimal("65920")),
]

SYNTHETIC_2024_FPL_HAWAII = [
    FPLGuideline(2024, "hawaii", 1, Decimal("17310")),
    FPLGuideline(2024, "hawaii", 2, Decimal("23500")),
    FPLGuideline(2024, "hawaii", 3, Decimal("29690")),
    FPLGuideline(2024, "hawaii", 4, Decimal("35880")),
    FPLGuideline(2024, "hawaii", 5, Decimal("42070")),
    FPLGuideline(2024, "hawaii", 6, Decimal("48260")),
    FPLGuideline(2024, "hawaii", 7, Decimal("54450")),
    FPLGuideline(2024, "hawaii", 8, Decimal("60640")),
]


def create_synthetic_resolver(year: int = 2024) -> PovertyGuidelineResolver:
    """Create a resolver with synthetic FPL data for testing."""
    resolver = PovertyGuidelineResolver()
    if year == 2024:
        for g in SYNTHETIC_2024_FPL_CONTIGUOUS:
            resolver.add_guideline(g)
        for g in SYNTHETIC_2024_FPL_ALASKA:
            resolver.add_guideline(g)
        for g in SYNTHETIC_2024_FPL_HAWAII:
            resolver.add_guideline(g)
    return resolver


class EligibilityEngine:
    """
    Deterministic eligibility engine for hospital financial assistance.

    Usage:
        engine = EligibilityEngine(fpl_resolver)
        result = engine.evaluate(policy, household_facts)
    """

    def __init__(self, fpl_resolver: PovertyGuidelineResolver | None = None):
        self.fpl_resolver = fpl_resolver or create_synthetic_resolver()

    def evaluate(
        self,
        policy: HospitalPolicy,
        household: HouseholdFacts,
        fpl_year: int | None = None,
        fpl_region: str | None = None,
    ) -> EligibilityResult:
        """
        Evaluate household against a hospital policy.

        Args:
            policy: Structured hospital policy with tiers
            household: Household facts
            fpl_year: Override policy's default FPL year
            fpl_region: Override policy's default FPL region

        Returns:
            EligibilityResult with status, explanation, and evidence
        """
        year = fpl_year or policy.default_fpl_year
        region = (fpl_region or policy.default_region).lower()

        # Get FPL for household size
        fpl_amount = self.fpl_resolver.get_fpl(year, region, household.household_size)

        result = EligibilityResult(
            status=EligibilityStatus.NEEDS_MORE_INFORMATION,
            explanation="",
            policy_id=policy.policy_id,
            household_size=household.household_size,
            annual_income_usd=household.annual_income_usd,
            fpl_used=fpl_amount,
            fpl_year=year,
            fpl_region=region,
        )

        # Handle missing FPL data
        if fpl_amount is None:
            result.status = EligibilityStatus.NEEDS_MORE_INFORMATION
            result.explanation = (
                f"FPL (Federal Poverty Level) data not available for year={year}, "
                f"region={region}, household_size={household.household_size}. "
                "Cannot complete income-based eligibility determination."
            )
            result.unresolved_rules.append(
                f"Missing FPL guideline for {year} {region} household size {household.household_size}"
            )
            return result

        # Evaluate each tier in priority order
        tier_evaluations = []
        missing_facts = set()
        unresolved_rules = set()
        higher_tier_pending = False  # True if a higher tier has missing (not failed) conditions

        for tier in sorted(policy.tiers, key=lambda t: t.priority):
            eval_result = self._evaluate_tier(tier, household, fpl_amount, year, region)
            tier_evaluations.append(eval_result)

            # Collect missing facts and unresolved rules
            missing_facts.update(eval_result.missing_conditions)
            unresolved_rules.update(eval_result.failed_conditions)

            # Check if this tier qualifies
            if eval_result.qualifies:
                # But first: if a higher tier had missing conditions, don't settle on this lower tier
                if higher_tier_pending:
                    result.tier_evaluations = tier_evaluations
                    result.missing_facts = sorted(missing_facts)
                    result.unresolved_rules = sorted(unresolved_rules)
                    result.status = EligibilityStatus.NEEDS_MORE_INFORMATION
                    result.explanation = (
                        f"Household income (${household.annual_income_usd:,.0f}) qualifies for "
                        f"'{tier.name}' but a higher-priority tier may still apply "
                        f"if missing information is provided. "
                        f"Missing facts: {', '.join(sorted(missing_facts))}."
                    )
                    result.evidence = self._build_evidence(None, None, household, fpl_amount, year, region)
                    return result

                result.matching_tier = tier
                result.tier_evaluations = tier_evaluations
                result.missing_facts = sorted(missing_facts)
                result.unresolved_rules = sorted(unresolved_rules)
                result.evidence = self._build_evidence(tier, eval_result, household, fpl_amount, year, region)

                income_str = f"${household.annual_income_usd:,.0f}"
                income_raw = str(household.annual_income_usd)
                if tier.type == "free":
                    result.status = EligibilityStatus.LIKELY_FREE
                    result.explanation = (
                        f"Household income ({income_str}) qualifies for "
                        f"free care under '{tier.name}' (threshold: {self._format_threshold(tier, fpl_amount)}). "
                        f"All verified conditions satisfied. Income: {income_raw}"
                    )
                else:
                    result.status = EligibilityStatus.LIKELY_DISCOUNTED
                    discount_info = ""
                    if tier.discount_percent is not None:
                        discount_info = f" with {tier.discount_percent}% discount"
                    elif tier.discount_formula:
                        discount_info = f" (discount: {tier.discount_formula})"
                    else:
                        discount_info = " (discount amount undetermined)"
                    result.explanation = (
                        f"Household income ({income_str}) qualifies for "
                        f"discounted care under '{tier.name}' (threshold: {self._format_threshold(tier, fpl_amount)})"
                        f"{discount_info}. All verified conditions satisfied. Income: {income_raw}"
                    )
                return result

            # Track if a higher-priority tier has missing (unknown) conditions that could change result
            # Only UNKNOWN (missing) conditions block lower tiers; NOT_SATISFIED (failed) do not
            if eval_result.income_qualifies is True and not eval_result.all_conditions_met:
                has_unknown = any(
                    state == ConditionState.UNKNOWN
                    for _, state in eval_result.condition_results
                )
                has_failed = any(
                    state == ConditionState.NOT_SATISFIED
                    for _, state in eval_result.condition_results
                )
                # Also check missing_conditions list (from threshold determination or explicit conditions)
                has_missing_threshold = any(
                    "threshold_determination" in mc for mc in eval_result.missing_conditions
                )

                if has_unknown or has_missing_threshold:
                    # Higher tier could still qualify if missing info provided - don't settle on lower
                    higher_tier_pending = True
                elif has_failed and not has_unknown:
                    # Higher tier's conditions failed - it's ruled out, continue to lower tiers
                    pass

        # No tier qualified
        result.tier_evaluations = tier_evaluations
        result.missing_facts = sorted(missing_facts)
        result.unresolved_rules = sorted(unresolved_rules)

        # Determine if we can rule out eligibility
        income_exceeds_all = all(
            te.income_qualifies is False for te in tier_evaluations if te.income_qualifies is not None
        )
        any_income_check_done = any(te.income_qualifies is not None for te in tier_evaluations)

        if income_exceeds_all and any_income_check_done:
            result.status = EligibilityStatus.PROBABLY_NOT_ELIGIBLE
            result.explanation = (
                f"Household income (${household.annual_income_usd:,.0f}) exceeds all assistance "
                f"thresholds in this policy. FPL reference: ${fpl_amount:,.0f} "
                f"({year} {region}, household size {household.household_size})."
            )
        else:
            result.status = EligibilityStatus.NEEDS_MORE_INFORMATION
            result.explanation = (
                f"Cannot determine eligibility with current information. "
                f"Household income: ${household.annual_income_usd:,.0f}. "
                f"FPL reference: ${fpl_amount:,.0f} ({year} {region}, household size {household.household_size}). "
                f"Missing facts: {', '.join(sorted(missing_facts)) or 'none'}. "
                f"Unresolved rules: {', '.join(sorted(unresolved_rules)) or 'none'}."
            )
        result.evidence = self._build_evidence(None, None, household, fpl_amount, year, region)
        return result

    def _evaluate_tier(
        self,
        tier: AssistanceTier,
        household: HouseholdFacts,
        fpl_amount: Decimal,
        year: int,
        region: str,
    ) -> TierEvaluation:
        """Evaluate a single assistance tier."""
        eval_result = TierEvaluation(tier=tier)

        # Income qualification
        income_qualifies, comparison = self._check_income_threshold(
            tier, household, fpl_amount
        )
        eval_result.income_qualifies = income_qualifies
        eval_result.income_comparison = comparison

        # If threshold couldn't be determined (e.g., missing table row), treat as unresolved
        if income_qualifies is None:
            eval_result.missing_conditions.append(f"threshold_determination: {comparison}")
            eval_result.failed_conditions.append(f"threshold_determination: {comparison}")
            eval_result.all_conditions_met = False
            eval_result.qualifies = False
            return eval_result

        if income_qualifies is False:
            return eval_result

        # Evaluate conditions
        all_met = True
        for condition in tier.conditions:
            state = self._check_condition(condition, household)
            eval_result.condition_results.append((condition, state))

            if state == ConditionState.SATISFIED:
                continue
            elif state == ConditionState.NOT_SATISFIED:
                all_met = False
                eval_result.failed_conditions.append(condition.name)
            elif state == ConditionState.UNKNOWN:
                all_met = False
                eval_result.missing_conditions.append(condition.name)
            elif state == ConditionState.NOT_APPLICABLE:
                # Doesn't affect qualification
                pass

        eval_result.all_conditions_met = all_met
        eval_result.qualifies = income_qualifies and all_met
        return eval_result

    def _check_income_threshold(
        self,
        tier: AssistanceTier,
        household: HouseholdFacts,
        fpl_amount: Decimal,
    ) -> tuple[Optional[bool], str]:
        """Check if income meets tier threshold. Returns (qualifies, comparison_string).

        Uses EXACT threshold for comparison logic (no rounding). Rounding only for display.
        """
        income = household.annual_income_usd
        if tier.threshold_type == ThresholdType.FPL_PERCENTAGE:
            # Use EXACT threshold for comparison (no quantization)
            exact_threshold = fpl_amount * (tier.threshold_value / Decimal("100"))

            # Only quantize for display purposes
            display_threshold = exact_threshold.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            if tier.inclusivity == Inclusivity.INCLUSIVE:
                qualifies = income <= exact_threshold
                op = "<="
            else:
                qualifies = income < exact_threshold
                op = "<"

            return qualifies, f"${income:,.2f} {op} ${display_threshold:,.2f} ({tier.threshold_value}% FPL)"

        elif tier.threshold_type == ThresholdType.FIXED_INCOME_TABLE:
            # threshold_value is the household_size index (1-based) or a direct amount
            # For fixed tables, we need the table data in tier.scope or elsewhere
            # This is a simplified implementation - in practice the table would be in scope
            table = tier.scope.get("income_table", {})
            if not table:
                return None, "No income table provided for fixed threshold"

            hs = str(household.household_size)
            if hs not in table:
                return None, f"No table entry for household size {household.household_size}"

            threshold = Decimal(str(table[hs]))

            if tier.inclusivity == Inclusivity.INCLUSIVE:
                qualifies = income <= threshold
                op = "<="
            else:
                qualifies = income < threshold
                op = "<"

            return qualifies, f"${income:,.2f} {op} ${threshold:,.2f} (fixed table, HH={household.household_size})"

        return None, "Unknown threshold type"

    def _check_condition(
        self,
        condition: PolicyCondition,
        household: HouseholdFacts,
    ) -> ConditionState:
        """Check a policy condition against household facts."""
        # If condition is explicitly marked as not applicable, return that
        if condition.state == ConditionState.NOT_APPLICABLE:
            return ConditionState.NOT_APPLICABLE

        name = condition.name.lower()

        # Residency conditions
        if "residen" in name:
            if condition.verified_value is not None:
                # Condition has a verified value from policy extraction
                required_state = condition.verified_value
                if household.residency_state and household.residency_state.upper() == required_state.upper():
                    return ConditionState.SATISFIED
                elif household.residency_state:
                    return ConditionState.NOT_SATISFIED
                return ConditionState.UNKNOWN
            else:
                # Just checking if residency is known
                if household.residency_state:
                    return ConditionState.SATISFIED
                return ConditionState.UNKNOWN

        # Asset test
        if "asset" in name:
            if household.assets_usd is not None:
                # If policy specifies an asset limit, it would be in verified_value
                if condition.verified_value is not None:
                    limit = Decimal(str(condition.verified_value))
                    if household.assets_usd <= limit:
                        return ConditionState.SATISFIED
                    return ConditionState.NOT_SATISFIED
                return ConditionState.SATISFIED  # Assets known, no specific limit
            return ConditionState.UNKNOWN

        # Insurance status
        if "insur" in name:
            if household.insurance_status:
                required = condition.verified_value
                if required and household.insurance_status.lower() == required.lower():
                    return ConditionState.SATISFIED
                elif required:
                    return ConditionState.NOT_SATISFIED
                return ConditionState.SATISFIED
            return ConditionState.UNKNOWN

        # Facility match
        if "facilit" in name:
            if household.facility_name and condition.verified_value:
                if household.facility_name.lower() in [f.lower() for f in condition.verified_value]:
                    return ConditionState.SATISFIED
                return ConditionState.NOT_SATISFIED
            return ConditionState.UNKNOWN

        # Service type
        if "service" in name or "care" in name:
            if household.service_type and condition.verified_value:
                if household.service_type.lower() == condition.verified_value.lower():
                    return ConditionState.SATISFIED
                return ConditionState.NOT_SATISFIED
            return ConditionState.UNKNOWN

        # Age
        if "age" in name:
            if household.patient_age is not None:
                if condition.verified_value is not None:
                    # Could be a min/max dict
                    if isinstance(condition.verified_value, dict):
                        min_age = condition.verified_value.get("min", 0)
                        max_age = condition.verified_value.get("max", 150)
                        if min_age <= household.patient_age <= max_age:
                            return ConditionState.SATISFIED
                        return ConditionState.NOT_SATISFIED
                return ConditionState.SATISFIED
            return ConditionState.UNKNOWN

        # Citizenship
        if "citizen" in name or "immigration" in name:
            if household.patient_citizenship:
                required = condition.verified_value
                if required and household.patient_citizenship.lower() == required.lower():
                    return ConditionState.SATISFIED
                elif required:
                    return ConditionState.NOT_SATISFIED
                return ConditionState.SATISFIED
            return ConditionState.UNKNOWN

        # Default: unknown condition type
        return ConditionState.UNKNOWN

    def _format_threshold(self, tier: AssistanceTier, fpl_amount: Decimal) -> str:
        """Format threshold for human-readable output."""
        if tier.threshold_type == ThresholdType.FPL_PERCENTAGE:
            threshold = fpl_amount * (tier.threshold_value / Decimal("100"))
            threshold = threshold.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            incl = "at or below" if tier.inclusivity == Inclusivity.INCLUSIVE else "below"
            return f"{incl} ${threshold:,.2f} ({tier.threshold_value}% FPL)"
        elif tier.threshold_type == ThresholdType.FIXED_INCOME_TABLE:
            return f"fixed income table (HH={tier.threshold_value})"
        return str(tier.threshold_value)

    def _build_evidence(
        self,
        matching_tier: AssistanceTier | None,
        tier_eval: TierEvaluation | None,
        household: HouseholdFacts,
        fpl_amount: Decimal,
        year: int = 2024,
        region: str = "contiguous",
    ) -> list[dict[str, Any]]:
        """Build evidence list for the result."""
        evidence = []

        # FPL reference - use correct key format (year, region, household_size)
        fpl_guideline = self.fpl_resolver._table.get((year, region.lower(), household.household_size))
        evidence.append({
            "type": "fpl_reference",
            "year": year if fpl_guideline is not None else None,
            "region": region,
            "household_size": household.household_size,
            "amount": str(fpl_amount),
        })

        if matching_tier and tier_eval:
            evidence.append({
                "type": "tier_rule",
                "tier_id": matching_tier.tier_id,
                "tier_name": matching_tier.name,
                "tier_type": matching_tier.type,
                "income_comparison": tier_eval.income_comparison,
                "threshold_value": str(matching_tier.threshold_value),
                "threshold_type": matching_tier.threshold_type.value,
                "inclusivity": matching_tier.inclusivity.value,
                "conditions": [
                    {
                        "name": c.name,
                        "description": c.description,
                        "state": s.value,
                        "evidence_ref": c.evidence_ref,
                    }
                    for c, s in tier_eval.condition_results
                ],
                "discount_percent": str(matching_tier.discount_percent) if matching_tier.discount_percent else None,
                "discount_formula": matching_tier.discount_formula,
                "source_ref": matching_tier.evidence_ref,
            })

        # Add all tier rules for transparency
        for te in (tier_eval.tier_evaluations if tier_eval and hasattr(tier_eval, 'tier_evaluations') else []):
            pass  # Already handled above

        return evidence


# Convenience function for simple usage
def evaluate_eligibility(
    policy: HospitalPolicy,
    household: HouseholdFacts,
    fpl_resolver: PovertyGuidelineResolver | None = None,
    fpl_year: int | None = None,
    fpl_region: str | None = None,
) -> EligibilityResult:
    """Convenience function to evaluate eligibility."""
    engine = EligibilityEngine(fpl_resolver)
    return engine.evaluate(policy, household, fpl_year, fpl_region)