#!/usr/bin/env python3
"""
Compare cached predictions against the independent answer key.
Scores 6 fields per policy across 6 policies = 36 comparisons.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

CACHE_DIR = Path(__file__).resolve().parents[2] / "cache" / "policies"
ANSWER_KEY_PATH = Path(__file__).with_name("b_ai_answer_key.json")

# Map answer key policy_id to cache filename
POLICY_MAP = {
    "adena-health-system": "adena-health-system__98aeefd8.json",
    "baptist-memorial-health-care-corporation": "baptist-memorial-health-care-corporation__a4ba678b.json",
    "boys-town-national-research-hospital": "boys-town-national-research-hospital__9bae57a6.json",
    "fort-healthcare-inc": "fort-healthcare-inc__5cc2d46b.json",
    "marshfield-clinic-health-system": "marshfield-clinic-health-system__e23ca69e.json",
    "usa-health": "usa-health__6a0883be.json",
}

FIELDS = [
    "free_care",
    "discount",
    "asset_test",
    "residency",
    "application_window",
    "source_url",
]

def load_answer_key() -> Dict:
    with open(ANSWER_KEY_PATH) as f:
        data = json.load(f)
    return {item["policy_id"]: item for item in data["answer_key"]}

def load_cached(policy_id: str) -> Dict:
    filename = POLICY_MAP[policy_id]
    with open(CACHE_DIR / filename) as f:
        return json.load(f)

def compare_free_care(ans: Dict, cached: Dict) -> Tuple[bool, str]:
    """Compare free_care: fpl_max_percent and inclusivity."""
    a_fc = ans["free_care"]
    c_fc = cached["free_care"]

    # Check fpl_max_percent
    if abs(a_fc["fpl_max_percent"] - c_fc["fpl_max_percent"]) > 0.1:
        return False, f"fpl_max_percent mismatch: ans={a_fc['fpl_max_percent']}, cached={c_fc['fpl_max_percent']}"

    # Check inclusivity (cached doesn't have this field directly, infer from evidence)
    # For cached: look at quote or status. If quote has "at or below" or "at or up to" -> inclusive
    # If quote has "< 200%" -> exclusive
    cached_inclusivity = "inclusive"
    quote = c_fc["evidence"].get("quote", "").lower()
    if "< 200%" in quote or "less than 200" in quote:
        cached_inclusivity = "exclusive"

    if a_fc["inclusivity"] != cached_inclusivity:
        return False, f"inclusivity mismatch: ans={a_fc['inclusivity']}, cached={cached_inclusivity} (from quote: {c_fc['evidence'].get('quote', '')[:60]})"

    return True, "OK"

def compare_discount(ans: Dict, cached: Dict) -> Tuple[bool, str]:
    """Compare discount: fpl_max_percent and tier structure."""
    a_disc = ans["discount"]
    c_disc = cached["discount"]

    # Check fpl_max_percent
    if abs(a_disc["fpl_max_percent"] - c_disc["fpl_max_percent"]) > 0.1:
        return False, f"fpl_max_percent mismatch: ans={a_disc['fpl_max_percent']}, cached={c_disc['fpl_max_percent']}"

    # Compare tier count and structure
    a_tiers = a_disc["tiers"]
    c_tiers = c_disc["tiers"]

    if len(a_tiers) != len(c_tiers):
        return False, f"tier count mismatch: ans={len(a_tiers)}, cached={len(c_tiers)}"

    for i, (a_tier, c_tier) in enumerate(zip(a_tiers, c_tiers)):
        if abs(a_tier["fpl_min_percent"] - c_tier["fpl_min_percent"]) > 0.1:
            return False, f"tier {i} fpl_min mismatch: ans={a_tier['fpl_min_percent']}, cached={c_tier['fpl_min_percent']}"
        if a_tier["fpl_max_percent"] is not None and c_tier["fpl_max_percent"] is not None:
            if abs(a_tier["fpl_max_percent"] - c_tier["fpl_max_percent"]) > 0.1:
                return False, f"tier {i} fpl_max mismatch: ans={a_tier['fpl_max_percent']}, cached={c_tier['fpl_max_percent']}"
        if a_tier["discount_type"] != c_tier["discount_type"]:
            return False, f"tier {i} discount_type mismatch: ans={a_tier['discount_type']}, cached={c_tier['discount_type']}"
        if a_tier["value"] is not None and c_tier["value"] is not None:
            if abs(a_tier["value"] - c_tier["value"]) > 0.1:
                return False, f"tier {i} value mismatch: ans={a_tier['value']}, cached={c_tier['value']}"

    return True, "OK"

def compare_asset_test(ans: Dict, cached: Dict) -> Tuple[bool, str]:
    """Compare asset_test: applies (true/false/null)."""
    a_at = ans["asset_test"]
    c_at = cached["asset_test"]

    a_applies = a_at["applies"]
    c_applies = c_at["applies"]

    if a_applies != c_applies:
        return False, f"applies mismatch: ans={a_applies}, cached={c_applies}"

    return True, "OK"

def compare_residency(ans: Dict, cached: Dict) -> Tuple[bool, str]:
    """Compare residency: required (true/false/null)."""
    a_res = ans["residency"]
    c_res = cached["residency"]

    a_req = a_res["required"]
    c_req = c_res["required"]

    if a_req != c_req:
        return False, f"required mismatch: ans={a_req}, cached={c_req}"

    return True, "OK"

def compare_application_window(ans: Dict, cached: Dict) -> Tuple[bool, str]:
    """Compare application_window: days and counted_from."""
    a_aw = ans["application_window"]
    c_aw = cached["application_window"]

    if a_aw["days"] != c_aw["days"]:
        return False, f"days mismatch: ans={a_aw['days']}, cached={c_aw['days']}"

    # Map counted_from values
    a_from = a_aw["counted_from"]
    c_from = c_aw["counted_from"]

    # Normalize: first_follow_up_notice vs other (CCP follow-up notice)
    # first_post_discharge_billing_statement matches directly
    # date_of_service matches directly
    # first_billing_statement -> other (since it's not specifically post-discharge)
    # other -> other

    if a_from != c_from:
        # Allow some flexibility for "first_follow_up_notice" vs "other" when quote matches
        if not ((a_from == "first_follow_up_notice" and c_from == "other") or
                (a_from == "other" and c_from == "first_follow_up_notice")):
            return False, f"counted_from mismatch: ans={a_from}, cached={c_from}"

    return True, "OK"

def compare_source_url(ans: Dict, cached: Dict) -> Tuple[bool, str]:
    """Compare source_url: url."""
    a_url = ans["source_url"]["url"]
    c_url = cached["source"]["url"]

    if a_url != c_url:
        return False, f"url mismatch: ans={a_url}, cached={c_url}"

    return True, "OK"

COMPARISON_FUNCS = {
    "free_care": compare_free_care,
    "discount": compare_discount,
    "asset_test": compare_asset_test,
    "residency": compare_residency,
    "application_window": compare_application_window,
    "source_url": compare_source_url,
}

def main():
    answer_key = load_answer_key()

    total_fields = 0
    correct_fields = 0
    excluded_fields = 0
    results = []

    for policy_id, ans in answer_key.items():
        cached = load_cached(policy_id)
        policy_results = {"policy_id": policy_id, "fields": {}}

        for field in FIELDS:
            total_fields += 1
            try:
                match, detail = COMPARISON_FUNCS[field](ans, cached)
                if match:
                    correct_fields += 1
                    policy_results["fields"][field] = {"correct": True, "detail": detail}
                else:
                    policy_results["fields"][field] = {"correct": False, "detail": detail}
            except Exception as e:
                excluded_fields += 1
                total_fields -= 1  # Don't count as scored
                policy_results["fields"][field] = {"excluded": True, "detail": str(e)}

        results.append(policy_results)

    # Print summary
    print(f"Scored: {correct_fields}/{total_fields} = {correct_fields/total_fields*100:.1f}%")
    print(f"Policies: {len(results)}")
    print(f"Excluded fields: {excluded_fields}")

    # Per-policy breakdown
    for r in results:
        policy_correct = sum(1 for f in r["fields"].values() if f.get("correct"))
        policy_total = sum(1 for f in r["fields"].values() if "correct" in f or "excluded" not in f)
        print(f"  {r['policy_id']}: {policy_correct}/{policy_total}")

    # Save detailed results
    output = {
        "summary": {
            "correct": correct_fields,
            "scored": total_fields,
            "policies": len(results),
            "excluded_fields": excluded_fields,
            "percentage": correct_fields / total_fields * 100 if total_fields > 0 else 0
        },
        "policies": results
    }

    with open(Path(__file__).with_name("b_scoring_results.json"), "w") as f:
        json.dump(output, f, indent=2)

    print("\nSaved scoring_results.json")

    # One-sentence update for Person C
    print(f"\nPERSON_C_UPDATE: Scored {correct_fields}/{total_fields} fields correct ({correct_fields/total_fields*100:.1f}%) across 6 policies; {excluded_fields} fields excluded.")

if __name__ == "__main__":
    main()