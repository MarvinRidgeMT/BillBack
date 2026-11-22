#!/usr/bin/env python
"""
Evaluation script for BillBack eligibility engine.
Loads policies and households from data/, runs the engine, and compares against answer key.
"""

import json
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any

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
    create_synthetic_resolver
)


def load_json(path: Path) -> dict:
    """Load JSON file."""
    with open(path, 'r') as f:
        return json.load(f)


def dict_to_policy(data: dict) -> HospitalPolicy:
    """Convert policy dict to HospitalPolicy object."""
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


def dict_to_household(data: dict) -> HouseholdFacts:
    """Convert household dict to HouseholdFacts object."""
    return HouseholdFacts(
        household_size=data["household_size"],
        annual_income_usd=Decimal(data["annual_income_usd"]),
        residency_state=data["residency_state"],
        residency_county=data["residency_county"],
        assets_usd=Decimal(data["assets_usd"]) if data["assets_usd"] else None,
        insurance_status=data["insurance_status"],
        facility_name=data["facility_name"],
        service_type=data["service_type"],
        patient_age=data["patient_age"],
        patient_citizenship=data["patient_citizenship"]
    )


def result_to_dict(result) -> dict:
    """Convert EligibilityResult to dict for comparison."""
    return {
        "status": result.status.value,
        "matching_tier": result.matching_tier.tier_id if result.matching_tier else None,
        "matching_tier_name": result.matching_tier.name if result.matching_tier else None,
        "matching_tier_type": result.matching_tier.type if result.matching_tier else None,
        "discount_percent": str(result.matching_tier.discount_percent) if result.matching_tier and result.matching_tier.discount_percent else None,
        "explanation": result.explanation,
        "missing_facts": result.missing_facts,
        "unresolved_rules": result.unresolved_rules
    }


def compare_results(expected: dict, actual: dict) -> tuple[bool, list[str]]:
    """Compare expected and actual results. Returns (match, list of differences)."""
    diffs = []

    for key in ["status", "matching_tier", "matching_tier_name", "matching_tier_type", "discount_percent"]:
        if expected.get(key) != actual.get(key):
            diffs.append(f"{key}: expected '{expected.get(key)}', got '{actual.get(key)}'")

    # Compare explanation (substring check for key terms)
    exp_explanation = expected.get("explanation", "").lower()
    act_explanation = actual.get("explanation", "").lower()

    # Check missing facts
    if set(expected.get("missing_facts", [])) != set(actual.get("missing_facts", [])):
        diffs.append(f"missing_facts: expected {expected.get('missing_facts')}, got {actual.get('missing_facts')}")

    # Check unresolved rules
    if set(expected.get("unresolved_rules", [])) != set(actual.get("unresolved_rules", [])):
        diffs.append(f"unresolved_rules: expected {expected.get('unresolved_rules')}, got {actual.get('unresolved_rules')}")

    return len(diffs) == 0, diffs


def main():
    data_dir = Path("data")
    policies_dir = data_dir / "policies"
    households_dir = data_dir / "households"
    answer_key_path = data_dir / "answer_key.json"

    # Load answer key
    answer_key = load_json(answer_key_path)

    # Load all policies
    policies = {}
    for policy_file in sorted(policies_dir.glob("*.json")):
        data = load_json(policy_file)
        policies[data["policy_id"]] = dict_to_policy(data)

    # Load all households
    households = {}
    for household_file in sorted(households_dir.glob("*.json")):
        data = load_json(household_file)
        households[data["household_id"]] = dict_to_household(data)

    # Create engine
    resolver = create_synthetic_resolver(2024)
    engine = EligibilityEngine(resolver)

    # Evaluate all combinations
    results = {}
    mismatches = []
    total = 0
    matched = 0

    print("Evaluating all policy-household combinations...")
    print("=" * 80)

    for policy_id in sorted(policies.keys()):
        for household_id in sorted(households.keys()):
            total += 1
            policy = policies[policy_id]
            household = households[household_id]

            try:
                result = engine.evaluate(policy, household)
                actual = result_to_dict(result)
            except Exception as e:
                actual = {
                    "status": "error",
                    "error": str(e),
                    "matching_tier": None,
                    "matching_tier_name": None,
                    "matching_tier_type": None,
                    "discount_percent": None,
                    "explanation": "",
                    "missing_facts": [],
                    "unresolved_rules": []
                }

            expected = answer_key["results"][policy_id][household_id]

            is_match, diffs = compare_results(expected, actual)

            if is_match:
                matched += 1
                status = "✓"
            else:
                status = "✗"
                mismatches.append({
                    "policy_id": policy_id,
                    "household_id": household_id,
                    "expected": expected,
                    "actual": actual,
                    "diffs": diffs
                })

            results[f"{policy_id}-{household_id}"] = {
                "policy_id": policy_id,
                "household_id": household_id,
                "match": is_match,
                "expected_status": expected.get("status"),
                "actual_status": actual.get("status"),
                "diffs": diffs
            }

            # Print progress
            if total % 20 == 0 or total == 200:
                print(f"  Processed {total}/200...")

    print("=" * 80)
    print(f"Results: {matched}/{total} combinations match answer key")

    if mismatches:
        print(f"\nMismatches ({len(mismatches)}):")
        for m in mismatches:
            print(f"\n  {m['policy_id']} + {m['household_id']}:")
            for diff in m['diffs']:
                print(f"    - {diff}")
    else:
        print("\nAll combinations match the answer key!")

    # Summary by status
    status_counts = {}
    for r in results.values():
        s = r["actual_status"]
        status_counts[s] = status_counts.get(s, 0) + 1

    print("\nStatus distribution:")
    for status, count in sorted(status_counts.items()):
        print(f"  {status}: {count}")

    # Summary by policy
    print("\nPer-policy summary:")
    for policy_id in sorted(policies.keys()):
        policy_results = [r for r in results.values() if r["policy_id"] == policy_id]
        policy_matches = sum(1 for r in policy_results if r["match"])
        print(f"  {policy_id}: {policy_matches}/{len(policy_results)} match")

    # Save detailed results
    output = {
        "summary": {
            "total_combinations": total,
            "matched": matched,
            "mismatched": len(mismatches),
            "status_distribution": status_counts
        },
        "details": results
    }

    with open(data_dir / "evaluation_results.json", 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\nDetailed results saved to {data_dir}/evaluation_results.json")

    return 0 if len(mismatches) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())