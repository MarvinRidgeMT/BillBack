#!/usr/bin/env python
"""
BillBack Eligibility Engine - Runnable Demo
============================================

This script demonstrates the eligibility engine with fictional policy data.
It loads a policy, creates a household, evaluates eligibility, and prints the result.
"""

import json
import sys
from decimal import Decimal
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from billback.eligibility import (
    EligibilityEngine,
    HospitalPolicy,
    AssistanceTier,
    PolicyCondition,
    HouseholdFacts,
    ThresholdType,
    Inclusivity,
    EligibilityStatus,
    create_synthetic_resolver,
)


def load_policy(policy_id: str) -> HospitalPolicy:
    """Load a policy from JSON file."""
    policy_path = Path(__file__).parent.parent / "data" / "policies" / f"{policy_id}.json"
    with open(policy_path, 'r') as f:
        data = json.load(f)

    # Convert to objects
    tiers = []
    for t in data["tiers"]:
        conditions = []
        for c in t["conditions"]:
            conditions.append(PolicyCondition(
                name=c["name"],
                description=c["description"],
                required=c["required"],
                verified_value=c["verified_value"],
                evidence_ref=c.get("evidence_ref")
            ))
        tiers.append(AssistanceTier(
            tier_id=t["tier_id"],
            name=t["name"],
            type=t["type"],
            threshold_type=ThresholdType(t["threshold_type"]),
            threshold_value=Decimal(t["threshold_value"]),
            inclusivity=Inclusivity(t["inclusivity"]),
            discount_percent=Decimal(t["discount_percent"]) if t["discount_percent"] else None,
            discount_formula=t["discount_formula"],
            conditions=conditions,
            scope=t["scope"],
            evidence_ref=t["evidence_ref"],
            priority=t["priority"]
        ))

    return HospitalPolicy(
        policy_id=data["policy_id"],
        hospital_name=data["hospital_name"],
        facility_names=data["facility_names"],
        state=data["state"],
        source_url=data["source_url"],
        retrieval_date=data["retrieval_date"],
        effective_date=data["effective_date"],
        version=data["version"],
        tiers=tiers,
        default_fpl_year=data["default_fpl_year"],
        default_region=data["default_region"]
    )


def create_household(
    household_size: int,
    annual_income: str,
    residency_state: str,
    residency_county: str = None,
    assets: str = "0",
    insurance_status: str = "uninsured",
    facility_name: str = None,
    service_type: str = "emergency",
    patient_age: int = 35,
    patient_citizenship: str = "citizen"
) -> HouseholdFacts:
    """Create a household facts object."""
    return HouseholdFacts(
        household_size=household_size,
        annual_income_usd=Decimal(annual_income),
        residency_state=residency_state,
        residency_county=residency_county,
        assets_usd=Decimal(assets) if assets else None,
        insurance_status=insurance_status,
        facility_name=facility_name,
        service_type=service_type,
        patient_age=patient_age,
        patient_citizenship=patient_citizenship
    )


def print_result(result, policy: HospitalPolicy, household: HouseholdFacts):
    """Print formatted eligibility result."""
    print("\n" + "=" * 60)
    print("ELIGIBILITY RESULT")
    print("=" * 60)
    print(f"Policy:          {policy.hospital_name} ({policy.policy_id})")
    print(f"State:           {policy.state}")
    print(f"Household Size:  {household.household_size}")
    print(f"Annual Income:   ${household.annual_income_usd:,.2f}")
    print(f"Residency:       {household.residency_state or 'Not provided'}")
    print(f"Assets:          ${household.assets_usd:,.2f}" if household.assets_usd else "Assets:          Not provided")
    print(f"Insurance:       {household.insurance_status}")
    print("-" * 60)
    print(f"Status:          {result.status.value}")

    if result.matching_tier:
        print(f"Matching Tier:   {result.matching_tier.tier_id} ({result.matching_tier.name})")
        print(f"Tier Type:       {result.matching_tier.type}")
        if result.matching_tier.discount_percent:
            print(f"Discount:        {result.matching_tier.discount_percent}%")
    else:
        print("Matching Tier:   None")

    print(f"Explanation:     {result.explanation}")

    if result.missing_facts:
        print(f"Missing Facts:   {', '.join(result.missing_facts)}")
    if result.unresolved_rules:
        print(f"Unresolved:      {', '.join(result.unresolved_rules)}")

    print("=" * 60)


def main():
    print("BillBack Eligibility Engine - Demo")
    print("==================================\n")

    # Create engine with synthetic 2024 FPL resolver
    resolver = create_synthetic_resolver(2024)
    engine = EligibilityEngine(resolver)

    # Demo 1: Single person at exactly 200% FPL (inclusive free tier)
    print("DEMO 1: Income exactly at inclusive free-care threshold")
    policy = load_policy("HOSP-001")  # General Medical Center, CA
    household = create_household(
        household_size=1,
        annual_income="30120",  # 200% of $15,060 = $30,120
        residency_state="CA",
        residency_county="Los Angeles",
        assets="5000"
    )
    result = engine.evaluate(policy, household)
    print_result(result, policy, household)

    # Demo 2: Just over free threshold, qualifies for discount
    print("\n\nDEMO 2: Income just over free threshold, qualifies for 75% discount")
    household2 = create_household(
        household_size=2,
        annual_income="40881",  # $1 over 200% FPL ($40,880)
        residency_state="CA",
        residency_county="Los Angeles",
        assets="15000"
    )
    result2 = engine.evaluate(policy, household2)
    print_result(result2, policy, household2)

    # Demo 3: Missing residency -> NEEDS_MORE_INFORMATION
    print("\n\nDEMO 3: Missing residency information")
    household3 = create_household(
        household_size=2,
        annual_income="35000",
        residency_state=None,  # Missing!
        assets="10000"
    )
    result3 = engine.evaluate(policy, household3)
    print_result(result3, policy, household3)

    # Demo 4: Alaska hospital with Alaska FPL
    print("\n\nDEMO 4: Alaska hospital, family of 4 at exactly 200% AK FPL")
    policy4 = load_policy("HOSP-009")  # Alaska Regional Hospital
    household4 = create_household(
        household_size=4,
        annual_income="78000",  # 200% of $39,000 (AK FPL for HH=4)
        residency_state="AK",
        residency_county="Anchorage"
    )
    result4 = engine.evaluate(policy4, household4)
    print_result(result4, policy4, household4)

    # Demo 5: Fixed income table (FL hospital)
    print("\n\nDEMO 5: Fixed income table - Florida hospital")
    policy5 = load_policy("HOSP-003")  # Sunshine State Hospital, FL
    household5 = create_household(
        household_size=1,
        annual_income="24000",  # Under $25,000 threshold for HH=1
        residency_state="FL",
        residency_county="Miami-Dade"
    )
    result5 = engine.evaluate(policy5, household5)
    print_result(result5, policy5, household5)

    print("\n\n✓ All demos completed successfully!")


if __name__ == "__main__":
    main()