"""Policy reader: accuracy vs the person-verified key, and how well the grounding check flags wrong fields.

- Grounding/sanity flags are recomputed in plain code on every cached real policy (no model call).
- Accuracy and the check's precision use ONLY rows of eval/verify/answer_key.csv that a person marked
  (is_correct yes/no AND verified_by filled in). With no verified rows, both are reported as pending.

    .venv/bin/python -m eval.policy_grounding   -> eval/results/policy_grounding.json
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path
from typing import Any, Optional

from backend.policy_reader import grounding
from backend.policy_reader.cache import DEFAULT_CACHE_DIR
from backend.policy_reader.schema import EVIDENCE_FIELDS, PolicyRules
from eval.common import REPO, run_meta, save_result
from eval.policy_benchmark import NO, YES

KEY = REPO / "eval" / "verify" / "answer_key.csv"
TARGET_FIELDS = 120  # 20 policies x 6 fields (the brief's benchmark size)
KEY_FIELD_TO_RULE = {
    "free_care %": "free_care", "discount max %": "discount", "discount tiers": "discount",
    "asset test": "asset_test", "residency": "residency", "application window": "application_window",
}


def cached_policies() -> dict[str, PolicyRules]:
    """hospital_name -> rules, for every cached policy."""
    return {r.hospital_name: r for r in (PolicyRules.model_validate_json(p.read_text())
                                         for p in sorted(Path(DEFAULT_CACHE_DIR).glob("*__*.json")))}


def flag_stats(policies: dict[str, PolicyRules]) -> dict[str, Any]:
    stated = verified = unverified = flagged = 0
    reasons: Counter[str] = Counter()
    per_policy = []
    for name, rules in policies.items():
        view = grounding.grounded_view(rules)
        n_flag = sum(f["needs_checking"] for f in view.values())
        per_policy.append({"hospital": name, "flagged": [k for k, f in view.items() if f["needs_checking"]]})
        flagged += n_flag
        for f in view.values():
            reasons.update(f["problems"])
            if f["status"] == "stated":
                stated += 1
                verified += f["verified"] is True
                unverified += f["verified"] is False
    return {"policies": len(policies), "fields": len(policies) * len(EVIDENCE_FIELDS), "stated": stated,
            "quotes_verified": verified, "quotes_not_found": unverified, "flagged": flagged,
            "flag_reasons": dict(reasons), "per_policy": per_policy}


def _verified_rows() -> list[dict[str, str]]:
    if not KEY.exists():
        return []
    rows = list(csv.DictReader(KEY.open(newline="")))
    return [r for r in rows if (r.get("is_correct") or "").strip().lower() in YES | NO and (r.get("verified_by") or "").strip()]


def accuracy_and_precision(policies: dict[str, PolicyRules]) -> dict[str, Any]:
    rows = _verified_rows()
    if not rows:
        return {"status": "pending", "verified_rows": 0, "key_rows": _key_size(), "target_fields": TARGET_FIELDS}
    correct = sum((r["is_correct"].strip().lower() in YES) for r in rows)
    flagged_rows, flagged_wrong, wrong_total, wrong_flagged = 0, 0, 0, 0
    for r in rows:
        rules = policies.get(r["hospital"])
        field = KEY_FIELD_TO_RULE.get(r["field"])
        if rules is None or field is None:
            continue
        is_flagged = grounding.grounded_view(rules)[field]["needs_checking"]
        is_wrong = r["is_correct"].strip().lower() in NO
        flagged_rows += is_flagged
        flagged_wrong += is_flagged and is_wrong
        wrong_total += is_wrong
        wrong_flagged += is_wrong and is_flagged
    return {
        "status": "measured", "verified_rows": len(rows), "key_rows": _key_size(), "target_fields": TARGET_FIELDS,
        "correct": correct, "policies_scored": len({r["hospital"] for r in rows}),
        "flagged_rows": flagged_rows, "flagged_and_wrong": flagged_wrong,
        "precision": (flagged_wrong / flagged_rows) if flagged_rows else None,
        "wrong_rows": wrong_total, "wrong_and_flagged": wrong_flagged,
        "recall": (wrong_flagged / wrong_total) if wrong_total else None,
    }


def _key_size() -> int:
    return sum(1 for _ in csv.DictReader(KEY.open(newline=""))) if KEY.exists() else 0


def main(argv: Optional[list[str]] = None) -> int:
    policies = cached_policies()
    payload = run_meta(flags=flag_stats(policies), accuracy=accuracy_and_precision(policies),
                       note="flags recomputed in code on cached reads; no model call")
    save_result("policy_grounding", payload)
    f, a = payload["flags"], payload["accuracy"]
    print(f"{f['policies']} policies: quotes verified {f['quotes_verified']}/{f['stated']} stated; flagged {f['flagged']}/{f['fields']} fields")
    print(f"accuracy: {a['status']} ({a['verified_rows']} verified rows of {a['key_rows']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
