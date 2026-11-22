"""
Scorer for Person A's Policy-Reader JSON
=========================================

This module validates and scores the JSON output from Person A's policy reader
before it's consumed by the eligibility engine.

Scoring Criteria:
- Completeness: All required fields present
- Consistency: Internal data consistency (tiers ordered by priority, no duplicate tier_ids, etc.)
- Validity: Enum values are valid, numeric values parse correctly
- Evidence: Required evidence_refs present for required conditions
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


@dataclass
class ScoreIssue:
    """Represents a single scoring issue."""
    severity: str  # "error", "warning", "info"
    category: str  # "completeness", "consistency", "validity", "evidence"
    message: str
    path: str  # JSON path to the issue (e.g., "tiers[0].threshold_value")


@dataclass
class PolicyScore:
    """Result of scoring a policy-reader JSON."""
    policy_id: str
    total_score: float  # 0.0 to 100.0
    max_score: float = 100.0
    issues: list[ScoreIssue] = field(default_factory=list)
    passed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "total_score": round(self.total_score, 1),
            "max_score": self.max_score,
            "passed": self.passed,
            "issues": [
                {
                    "severity": i.severity,
                    "category": i.category,
                    "message": i.message,
                    "path": i.path
                }
                for i in self.issues
            ],
            "summary": {
                "errors": sum(1 for i in self.issues if i.severity == "error"),
                "warnings": sum(1 for i in self.issues if i.severity == "warning"),
                "info": sum(1 for i in self.issues if i.severity == "info"),
            }
        }


class PolicyScorer:
    """
    Scores Person A's policy-reader JSON output.

    The policy-reader JSON format (from handoff_demo.py):
    {
      "policy_id": "HOSP-001",
      "hospital_name": "General Medical Center",
      "facility_names": ["General Medical Center Main", "GMC West Campus"],
      "state": "CA",
      "source_url": "https://example.com/gmc-policy.pdf",
      "retrieval_date": "2024-01-15",
      "effective_date": "2024-01-01",
      "version": "2024.1",
      "default_fpl_year": 2024,
      "default_region": "contiguous",
      "tiers": [
        {
          "tier_id": "free-200",
          "name": "Free Care - 200% FPL",
          "type": "free",
          "threshold_type": "fpl_percentage",
          "threshold_value": "200",
          "inclusivity": "inclusive",
          "discount_percent": null,
          "discount_formula": null,
          "conditions": [
            {"name": "residency", "description": "California resident", "required": true, "verified_value": "CA", "evidence_ref": "Sec 2.1"},
            {"name": "asset_test", "description": "Assets under $50,000", "required": true, "verified_value": "50000", "evidence_ref": "Sec 2.2"}
          ],
          "scope": {},
          "evidence_ref": "Page 3, Section 2",
          "priority": 0
        }
      ]
    }
    """

    # Required top-level fields
    REQUIRED_FIELDS = [
        "policy_id", "hospital_name", "facility_names", "state",
        "source_url", "retrieval_date", "effective_date", "version",
        "default_fpl_year", "default_region", "tiers"
    ]

    # Required tier fields
    REQUIRED_TIER_FIELDS = [
        "tier_id", "name", "type", "threshold_type", "threshold_value",
        "inclusivity", "conditions", "scope", "evidence_ref", "priority"
    ]

    # Valid enum values
    VALID_TIER_TYPES = {"free", "discounted"}
    VALID_THRESHOLD_TYPES = {"fpl_percentage", "fixed_income", "fixed_income_table"}
    VALID_INCLUSIVITY = {"inclusive", "exclusive"}
    VALID_REGIONS = {"contiguous", "alaska", "hawaii"}

    def __init__(self):
        self.issues: list[ScoreIssue] = []
        self._score = 100.0

    def score(self, policy_data: dict[str, Any]) -> PolicyScore:
        """Score a policy-reader JSON dict."""
        self.issues = []
        self._score = 100.0

        policy_id = policy_data.get("policy_id", "UNKNOWN")

        # Run all scoring checks
        self._check_completeness(policy_data)
        self._check_validity(policy_data)
        self._check_consistency(policy_data)
        self._check_evidence(policy_data)

        # Determine pass/fail (no errors = pass)
        has_errors = any(i.severity == "error" for i in self.issues)

        return PolicyScore(
            policy_id=policy_id,
            total_score=max(0.0, self._score),
            issues=self.issues,
            passed=not has_errors
        )

    def score_file(self, path: Path | str) -> PolicyScore:
        """Score a policy-reader JSON file."""
        with open(path, 'r') as f:
            policy_data = json.load(f)
        return self.score(policy_data)

    def _add_issue(self, severity: str, category: str, message: str, path: str, penalty: float = 0):
        """Add an issue and apply penalty to score."""
        self.issues.append(ScoreIssue(severity, category, message, path))
        if severity == "error":
            self._score -= penalty if penalty > 0 else 10.0
        elif severity == "warning":
            self._score -= penalty if penalty > 0 else 5.0
        elif severity == "info":
            self._score -= penalty if penalty > 0 else 1.0
        self._score = max(0.0, self._score)

    def _check_completeness(self, data: dict[str, Any]) -> None:
        """Check that all required fields are present."""
        for field_name in self.REQUIRED_FIELDS:
            if field_name not in data:
                self._add_issue("error", "completeness",
                    f"Missing required field: {field_name}", field_name, 10.0)
            elif data[field_name] is None:
                self._add_issue("error", "completeness",
                    f"Required field is null: {field_name}", field_name, 10.0)

        # Check tiers array
        tiers = data.get("tiers", [])
        if not isinstance(tiers, list):
            self._add_issue("error", "completeness",
                "'tiers' must be a list", "tiers", 10.0)
            return

        if len(tiers) == 0:
            self._add_issue("warning", "completeness",
                "Policy has no tiers defined", "tiers", 5.0)

        for i, tier in enumerate(tiers):
            tier_path = f"tiers[{i}]"
            for field_name in self.REQUIRED_TIER_FIELDS:
                if field_name not in tier:
                    self._add_issue("error", "completeness",
                        f"Tier missing required field: {field_name}", f"{tier_path}.{field_name}", 5.0)
                elif tier[field_name] is None and field_name not in ("discount_percent", "discount_formula"):
                    self._add_issue("error", "completeness",
                        f"Tier required field is null: {field_name}", f"{tier_path}.{field_name}", 5.0)

            # Check conditions
            conditions = tier.get("conditions", [])
            if not isinstance(conditions, list):
                self._add_issue("error", "completeness",
                    f"Tier 'conditions' must be a list", f"{tier_path}.conditions", 5.0)
            else:
                for j, cond in enumerate(conditions):
                    cond_path = f"{tier_path}.conditions[{j}]"
                    required_cond_fields = ["name", "description", "required", "verified_value"]
                    for cfield in required_cond_fields:
                        if cfield not in cond:
                            self._add_issue("error", "completeness",
                                f"Condition missing required field: {cfield}", f"{cond_path}.{cfield}", 3.0)

    def _check_validity(self, data: dict[str, Any]) -> None:
        """Check that field values are valid."""
        # Validate state (2-letter code)
        state = data.get("state")
        if state and (not isinstance(state, str) or len(state) != 2):
            self._add_issue("warning", "validity",
                f"State should be 2-letter code, got: {state}", "state", 3.0)

        # Validate default_region
        region = data.get("default_region")
        if region and region not in self.VALID_REGIONS:
            self._add_issue("error", "validity",
                f"Invalid default_region: {region}. Must be one of {self.VALID_REGIONS}", "default_region", 5.0)

        # Validate default_fpl_year
        year = data.get("default_fpl_year")
        if year is not None:
            if not isinstance(year, int) or year < 2000 or year > 2100:
                self._add_issue("warning", "validity",
                    f"default_fpl_year should be a reasonable year, got: {year}", "default_fpl_year", 2.0)

        # Validate tiers
        tiers = data.get("tiers", [])
        for i, tier in enumerate(tiers):
            tier_path = f"tiers[{i}]"

            # tier_type
            ttype = tier.get("type")
            if ttype and ttype not in self.VALID_TIER_TYPES:
                self._add_issue("error", "validity",
                    f"Invalid tier type: {ttype}. Must be one of {self.VALID_TIER_TYPES}", f"{tier_path}.type", 5.0)

            # threshold_type
            thresh_type = tier.get("threshold_type")
            if thresh_type and thresh_type not in self.VALID_THRESHOLD_TYPES:
                self._add_issue("error", "validity",
                    f"Invalid threshold_type: {thresh_type}. Must be one of {self.VALID_THRESHOLD_TYPES}", f"{tier_path}.threshold_type", 5.0)

            # inclusivity
            inclusivity = tier.get("inclusivity")
            if inclusivity and inclusivity not in self.VALID_INCLUSIVITY:
                self._add_issue("error", "validity",
                    f"Invalid inclusivity: {inclusivity}. Must be one of {self.VALID_INCLUSIVITY}", f"{tier_path}.inclusivity", 5.0)

            # threshold_value - must be valid decimal
            thresh_val = tier.get("threshold_value")
            if thresh_val is not None:
                try:
                    Decimal(str(thresh_val))
                except (InvalidOperation, ValueError):
                    self._add_issue("error", "validity",
                        f"threshold_value must be a valid number, got: {thresh_val}", f"{tier_path}.threshold_value", 5.0)

            # discount_percent - if present, must be valid decimal 0-100
            discount = tier.get("discount_percent")
            if discount is not None:
                try:
                    d = Decimal(str(discount))
                    if d < 0 or d > 100:
                        self._add_issue("error", "validity",
                            f"discount_percent must be 0-100, got: {discount}", f"{tier_path}.discount_percent", 3.0)
                except (InvalidOperation, ValueError):
                    self._add_issue("error", "validity",
                        f"discount_percent must be a valid number, got: {discount}", f"{tier_path}.discount_percent", 3.0)

            # priority - must be non-negative integer
            priority = tier.get("priority")
            if priority is not None:
                if not isinstance(priority, int) or priority < 0:
                    self._add_issue("warning", "validity",
                        f"priority should be non-negative integer, got: {priority}", f"{tier_path}.priority", 2.0)

            # conditions
            conditions = tier.get("conditions", [])
            for j, cond in enumerate(conditions):
                cond_path = f"{tier_path}.conditions[{j}]"
                required = cond.get("required")
                if required is not None and not isinstance(required, bool):
                    self._add_issue("error", "validity",
                        f"Condition 'required' must be boolean, got: {required}", f"{cond_path}.required", 3.0)

                verified = cond.get("verified_value")
                if verified is not None and not isinstance(verified, str):
                    self._add_issue("warning", "validity",
                        f"Condition 'verified_value' should be string, got: {type(verified).__name__}", f"{cond_path}.verified_value", 1.0)

    def _check_consistency(self, data: dict[str, Any]) -> None:
        """Check internal consistency of the policy."""
        tiers = data.get("tiers", [])

        # Check for duplicate tier_ids
        tier_ids = [t.get("tier_id") for t in tiers if t.get("tier_id")]
        duplicates = [tid for tid in set(tier_ids) if tier_ids.count(tid) > 1]
        for dup in duplicates:
            self._add_issue("error", "consistency",
                f"Duplicate tier_id: {dup}", "tiers[*].tier_id", 5.0)

        # Check priority ordering (lower = higher priority)
        priorities = [(t.get("priority", 999), t.get("tier_id", f"index-{i}")) for i, t in enumerate(tiers)]
        sorted_by_priority = sorted(priorities)
        if priorities != sorted_by_priority:
            self._add_issue("warning", "consistency",
                "Tiers not ordered by priority (lower priority number = higher priority). Engine will sort automatically.",
                "tiers[*].priority", 2.0)

        # Check that free tiers have no discount_percent
        for i, tier in enumerate(tiers):
            if tier.get("type") == "free" and tier.get("discount_percent") is not None:
                self._add_issue("warning", "consistency",
                    f"Free tier '{tier.get('tier_id')}' has discount_percent set (should be null)",
                    f"tiers[{i}].discount_percent", 2.0)

            # Discounted tiers should have discount_percent or discount_formula
            if tier.get("type") == "discounted":
                if tier.get("discount_percent") is None and tier.get("discount_formula") is None:
                    self._add_issue("warning", "consistency",
                        f"Discounted tier '{tier.get('tier_id')}' has neither discount_percent nor discount_formula",
                        f"tiers[{i}]", 3.0)

        # Check threshold_value makes sense for threshold_type
        for i, tier in enumerate(tiers):
            thresh_type = tier.get("threshold_type")
            thresh_val = tier.get("threshold_value")
            if thresh_type == "fpl_percentage" and thresh_val is not None:
                try:
                    val = Decimal(str(thresh_val))
                    if val <= 0 or val > 1000:
                        self._add_issue("warning", "consistency",
                            f"FPL percentage threshold unusual: {val}% (expected 100-500)",
                            f"tiers[{i}].threshold_value", 1.0)
                except (InvalidOperation, ValueError):
                    pass  # Already caught in validity check
            elif thresh_type in ("fixed_income", "fixed_income_table") and thresh_val is not None:
                try:
                    val = Decimal(str(thresh_val))
                    if val <= 0:
                        self._add_issue("warning", "consistency",
                            f"Fixed income threshold must be positive: {val}",
                            f"tiers[{i}].threshold_value", 2.0)
                except (InvalidOperation, ValueError):
                    pass

    def _check_evidence(self, data: dict[str, Any]) -> None:
        """Check evidence references are present for required conditions."""
        tiers = data.get("tiers", [])

        for i, tier in enumerate(tiers):
            tier_path = f"tiers[{i}]"
            tier_id = tier.get("tier_id", f"index-{i}")

            # Check tier-level evidence_ref
            if not tier.get("evidence_ref"):
                self._add_issue("warning", "evidence",
                    f"Tier '{tier_id}' missing evidence_ref", f"{tier_path}.evidence_ref", 2.0)

            # Check condition evidence_refs for required conditions
            conditions = tier.get("conditions", [])
            for j, cond in enumerate(conditions):
                cond_path = f"{tier_path}.conditions[{j}]"
                if cond.get("required", False):
                    if not cond.get("evidence_ref"):
                        self._add_issue("warning", "evidence",
                            f"Required condition '{cond.get('name')}' missing evidence_ref",
                            f"{cond_path}.evidence_ref", 2.0)


def score_policy_file(path: Path | str) -> PolicyScore:
    """Convenience function to score a single policy file."""
    scorer = PolicyScorer()
    return scorer.score_file(path)


def score_policy_dict(policy_data: dict[str, Any]) -> PolicyScore:
    """Convenience function to score a policy dict."""
    scorer = PolicyScorer()
    return scorer.score(policy_data)


def score_all_policies(directory: Path | str) -> dict[str, PolicyScore]:
    """Score all policy JSON files in a directory."""
    results = {}
    dir_path = Path(directory)
    for policy_file in sorted(dir_path.glob("*.json")):
        scorer = PolicyScorer()
        score = scorer.score_file(policy_file)
        results[policy_file.stem] = score
    return results


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m billback.scorer <policy_json_file_or_directory>")
        sys.exit(1)

    path = Path(sys.argv[1])

    if path.is_dir():
        results = score_all_policies(path)
        for policy_id, score in results.items():
            print(f"\n{'='*60}")
            print(f"Policy: {policy_id}")
            print(f"Score: {score.total_score:.1f}/100")
            print(f"Passed: {score.passed}")
            print(f"Issues: {score.to_dict()['summary']}")
            for issue in score.issues:
                print(f"  [{issue.severity.upper()}] {issue.category}: {issue.message} ({issue.path})")
    else:
        score = score_policy_file(path)
        print(json.dumps(score.to_dict(), indent=2))
        sys.exit(0 if score.passed else 1)