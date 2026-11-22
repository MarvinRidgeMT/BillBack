#!/usr/bin/env python
"""
Handoff Demo: Person B → Person A
===================================
This is a standalone, runnable snippet showing the exact test case:
"Income exactly at an inclusive free-care threshold"

This demonstrates the contract between Person B's eligibility engine
and Person A's policy reader + FPL data.

Run with: python scripts/handoff_demo.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from decimal import Decimal
from billback.eligibility import (
    EligibilityEngine,
    EligibilityStatus,
    ThresholdType,
    Inclusivity,
    HospitalPolicy,
    AssistanceTier,
    HouseholdFacts,
    FPLGuideline,
    PovertyGuidelineResolver,
    create_synthetic_resolver,
)


# ═══════════════════════════════════════════════════════════════════════════
# STEP 1: FPL DATA — Where Person A's fpl_2026.json plugs in
# ════════════════════════════════════════════════════════════════════════════
# For testing, we use synthetic 2024 FPL data built into the engine.
# In production, Person A provides a JSON file like fpl_2026.json:
#
# fpl_2026.json structure:
# [
#   {"year": 2026, "region": "contiguous", "household_size": 1, "annual_amount_usd": "15650"},
#   {"year": 2026, "region": "contiguous", "household_size": 2, "annual_amount_usd": "21150"},
#   ...
# ]
#
# Person A loads it like this:
#   import json
#   with open("fpl_2026.json") as f:
#       fpl_data = json.load(f)
#   guidelines = [FPLGuideline(**item) for item in fpl_data]
#   fpl_resolver = PovertyGuidelineResolver(guidelines)

fpl_resolver = create_synthetic_resolver(2024)  # ← swap for Person A's resolver


# ════════════════════════════════════════════════════════════════════════════
# STEP 2: HOSPITAL POLICY — Where Person A's policy-reader JSON plugs in
# ════════════════════════════════════════════════════════════════════════════
# Person A's policy reader outputs JSON like:
#
# policy_reader_output.json:
# {
#   "policy_id": "HOSP-001",
#   "hospital_name": "General Medical Center",
#   "facility_names": ["General Medical Center Main", "GMC West Campus"],
#   "state": "CA",
#   "source_url": "https://example.com/gmc-policy.pdf",
#   "retrieval_date": "2024-01-15",
#   "effective_date": "2024-01-01",
#   "version": "2024.1",
#   "default_fpl_year": 2024,
#   "default_region": "contiguous",
#   "tiers": [
#     {
#       "tier_id": "free-200",
#       "name": "Free Care - 200% FPL",
#       "type": "free",
#       "threshold_type": "fpl_percentage",
#       "threshold_value": "200",
#       "inclusivity": "inclusive",
#       "discount_percent": null,
#       "discount_formula": null,
#       "conditions": [
#         {"name": "residency", "description": "California resident", "required": true, "verified_value": "CA", "evidence_ref": "Sec 2.1"},
#         {"name": "asset_test", "description": "Assets under $50,000", "required": true, "verified_value": "50000", "evidence_ref": "Sec 2.2"}
#       ],
#       "scope": {},
#       "evidence_ref": "Page 3, Section 2",
#       "priority": 0
#     }
#   ]
# }
#
# Person A loads it like this:
#   with open("policy_reader_output.json") as f:
#       policy_data = json.load(f)
#   # Convert dicts → dataclasses (see conversion helpers below)

# This test uses a minimal in-memory policy equivalent to the JSON above:
policy = HospitalPolicy(
    policy_id="TEST-001",
    hospital_name="Test Hospital",
    facility_names=["Test Hospital Main"],
    state="CA",
    source_url="https://example.com/policy.pdf",
    retrieval_date="2024-01-15",
    effective_date="2024-01-01",
    default_fpl_year=2024,
    default_region="contiguous",
    tiers=[
        AssistanceTier(
            tier_id="free-200",
            name="Free Care - 200% FPL",
            type="free",
            threshold_type=ThresholdType.FPL_PERCENTAGE,
            threshold_value=Decimal("200"),
            inclusivity=Inclusivity.INCLUSIVE,
            evidence_ref="Page 3, Section 2.1",
            priority=0,
        ),
    ],
)


# ════════════════════════════════════════════════════════════════════════════
# STEP 3: HOUSEHOLD FACTS — Input from the patient/screener
# ════════════════════════════════════════════════════════════════════════════
# 2024 contiguous FPL for household of 2 = $20,440
# 200% FPL = $40,880
# This household earns EXACTLY $40,880 — right at the inclusive threshold.
household = HouseholdFacts(
    household_size=2,
    annual_income_usd=Decimal("40880"),
    residency_state="CA",  # optional but provided
    assets_usd=Decimal("5000"),  # optional
    insurance_status="uninsured",
)


# ════════════════════════════════════════════════════════════════════════════
# STEP 4: RUN THE ENGINE
# ════════════════════════════════════════════════════════════════════════════
engine = EligibilityEngine(fpl_resolver)
result = engine.evaluate(policy, household)


# ════════════════════════════════════════════════════════════════════════════
# STEP 5: ACTUAL RESULT (printed as JSON for Person A to verify)
# ════════════════════════════════════════════════════════════════════════════
print("=" * 70)
print("HANDOFF DEMO: Income exactly at inclusive free-care threshold")
print("=" * 70)
print()
print("INPUTS:")
print(f"  Policy: {policy.hospital_name} ({policy.policy_id})")
print(f"  Tier: {policy.tiers[0].name} ({policy.tiers[0].threshold_value}% FPL, {policy.tiers[0].inclusivity.value})")
print(f"  Household: size={household.household_size}, income=${household.annual_income_usd}")
print(f"  FPL Used: ${result.fpl_used:,.2f} ({result.fpl_year} {result.fpl_region}, HH={result.household_size})")
print()
print("OUTPUT (result.to_dict()):")
print("-" * 70)
import json
print(json.dumps(result.to_dict(), indent=2))
print()
print("=" * 70)
print("EXPECTED: status=likely_free, matching_tier=free-200")
print("=" * 70)

# Verify
assert result.status == EligibilityStatus.LIKELY_FREE, f"Expected LIKELY_FREE, got {result.status}"
assert result.matching_tier.tier_id == "free-200", f"Expected free-200, got {result.matching_tier.tier_id}"
assert "40880" in result.explanation, f"Raw income not in explanation: {result.explanation}"
print("✓ All assertions passed!")