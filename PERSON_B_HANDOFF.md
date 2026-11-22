# PERSON_B_HANDOFF.md

**BillBack Eligibility Engine — Handoff for Person A**  
Branch: `person-b-eligibility` | Date: 2026-11-22

---

## 1. Quick-Start Commands (PowerShell)

```powershell
# Navigate to project
cd C:\Users\abhi1_gxlm8t4\Documents\EvoHacks2

# Activate virtual environment
.venv\Scripts\Activate.ps1

# Run all pytest tests (36 tests)
python -m pytest tests/test_eligibility.py -v

# Run evaluation against answer key (200 combinations)
python scripts/evaluate.py

# Run scorer on all 20 synthetic policies
python -m billback.scorer data/policies

# Run scorer on 20 real policies (all unverified)
python -m billback.scorer data/real-policies

# Run independent household validation (10 manual-calc cases)
python scripts/independent_households.py

# Run demo (5 scenarios)
python scripts/demo.py
```

---

## 2. Engine Import Path

```python
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
    FPLGuideline,
    PovertyGuidelineResolver,
    create_synthetic_resolver,
    evaluate_eligibility,
)
from decimal import Decimal
```

---

## 3. Complete I/O Example

### 3.1 Policy JSON (`data/policies/HOSP-001.json`)

```json
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
    },
    {
      "tier_id": "discount-300",
      "name": "75% Discount - 300% FPL",
      "type": "discounted",
      "threshold_type": "fpl_percentage",
      "threshold_value": "300",
      "inclusivity": "inclusive",
      "discount_percent": "75",
      "discount_formula": null,
      "conditions": [
        {"name": "residency", "description": "California resident", "required": true, "verified_value": "CA", "evidence_ref": "Sec 3.1"}
      ],
      "scope": {},
      "evidence_ref": "Page 4, Section 3",
      "priority": 1
    },
    {
      "tier_id": "discount-400",
      "name": "50% Discount - 400% FPL",
      "type": "discounted",
      "threshold_type": "fpl_percentage",
      "threshold_value": "400",
      "inclusivity": "inclusive",
      "discount_percent": "50",
      "discount_formula": null,
      "conditions": [],
      "scope": {},
      "evidence_ref": "Page 5, Section 4",
      "priority": 2
    }
  ]
}
```

### 3.2 Household JSON (`data/households/HH-001.json`)

```json
{
  "household_id": "HH-001",
  "household_size": 1,
  "annual_income": "30120",
  "state": "CA",
  "assets": "5000",
  "insurance_status": "uninsured",
  "residency_state": "CA"
}
```

### 3.3 Result JSON (from `EligibilityResult.to_dict()`)

```json
{
  "policy_id": "HOSP-001",
  "household_id": "HH-001",
  "status": "likely_free",
  "matching_tier_id": "free-200",
  "matching_tier_type": "free",
  "discount_percent": null,
  "explanation": "Household income ($30,120) qualifies for free care under 'Free Care - 200% FPL' (threshold: at or below $30,120.00 (200% FPL)). All verified conditions satisfied. Income: 30120",
  "evidence": [
    {
      "tier_id": "free-200",
      "tier_name": "Free Care - 200% FPL",
      "condition": "residency",
      "state": "satisfied",
      "message": "Household residency CA matches required CA",
      "evidence_ref": "Sec 2.1"
    },
    {
      "tier_id": "free-200",
      "tier_name": "Free Care - 200% FPL",
      "condition": "asset_test",
      "state": "satisfied",
      "message": "Household assets 5000 <= threshold 50000",
      "evidence_ref": "Sec 2.2"
    }
  ],
  "missing_facts": [],
  "income_vs_threshold": {
    "tier_id": "free-200",
    "threshold_type": "fpl_percentage",
    "threshold_value": "200",
    "inclusivity": "inclusive",
    "fpl_used": 15060,
    "calculated_threshold": "30120.00",
    "household_income": "30120",
    "comparison": "30120 <= 30120.00"
  }
}
```

### 3.4 Minimal Python Usage

```python
from billback.eligibility import (
    HospitalPolicy, HouseholdFacts, create_synthetic_resolver, evaluate_eligibility
)
import json

# Load policy and household
with open('data/policies/HOSP-001.json') as f:
    policy_data = json.load(f)
with open('data/households/HH-001.json') as f:
    household_data = json.load(f)

policy = HospitalPolicy.from_dict(policy_data)
household = HouseholdFacts.from_dict(household_data)
resolver = create_synthetic_resolver()

result = evaluate_eligibility(policy, household, resolver)

print(f"Status: {result.status.value}")
print(f"Tier: {result.matching_tier_id}")
print(f"Explanation: {result.explanation}")
```

---

## 4. Ordered Checklist for Person A (Tomorrow)

| # | Task | Command / Action | Expected Outcome |
|---|------|------------------|------------------|
| 1 | **Verify environment** | `cd EvoHacks2 && .venv\Scripts\Activate.ps1 && python -c "import billback; print('OK')"`` | Imports without error |
| 2 | **Run full test suite** | `python -m pytest tests/test_eligibility.py -v` | **36 passed** |
| 3 | **Run evaluation** | `python scripts/evaluate.py` | **200/200 match** answer key |
| 4 | **Validate scorer** | `python -m billback.scorer data/policies` | **20 policies × 100/100** |
| 5 | **Run independent tests** | `python scripts/independent_households.py` | **10/10 PASS** |
| 6 | **Run demo** | `python scripts/demo.py` | **5 scenarios print** clean output |
| 7 | **Load a real policy** | `python -c "import json; from billback.eligibility import HospitalPolicy; p=HospitalPolicy.from_dict(json.load(open('data/real-policies/HOSP-R001.json'))); print(p.policy_id, p.hospital_name)"` | Prints `HOSP-R001 Kaiser Permanente` |
| 8 | **Score a real policy** | `python -m billback.scorer data/real-policies/HOSP-R001.json` | Score < 100 (evidence refs marked UNVERIFIED) |
| 9 | **Test engine on real policy** | Write quick script using `evaluate_eligibility()` with a real policy + household | Returns `EligibilityResult` with `verification_status="unverified"` in explanation |
| 10 | **Deliver Person A's reader output** | Place JSON files in `data/person_a_output/` matching schema in `billback/scorer.py` | Files score 100/100 on completeness, validity, consistency, evidence |

---

## 5. Key Engine Behaviors (Must-Know)

| Behavior | Detail |
|----------|--------|
| **Threshold comparison** | Uses exact `Decimal` threshold for logic; quantizes only for display |
| **Inclusivity** | `inclusive` = `<=` ; `exclusive` = `<` |
| **Tier priority** | Lower `priority` number = higher priority (0 = highest) |
| **Condition states** | `SATISFIED`, `NOT_SATISFIED`, `UNKNOWN`, `NOT_APPLICABLE` |
| **Higher-tier fallback** | If higher tier has missing/failed condition → engine tries next tier |
| **FPL regions** | `contiguous`, `alaska`, `hawaii` (synthetic 2024 guidelines) |
| **Evidence preservation** | Every condition check emits evidence with `evidence_ref` for audit trail |

---

## 6. File Inventory (What to Commit)

```
billback/
  eligibility.py      # Core engine (685 lines)
  scorer.py           # PolicyScorer for Person A's JSON
  __init__.py
tests/
  test_eligibility.py # 36 tests (33 original + 3 regression)
data/
  policies/           # 20 synthetic policies (HOSP-001..020)
  households/         # 10 household test cases (HH-001..010)
  answer_key.json     # 200 expected results
  evaluation_results.json
  real-policies/      # 20 real hospital policies (HOSP-R001..020, all unverified)
scripts/
  create_policies.py  # Generates synthetic policies + households + answer key
  evaluate.py         # Runs engine vs answer key
  independent_households.py # 10 manual-calc verification cases
  demo.py             # 5 demonstration scenarios
  handoff_demo.py     # Person A reader output format example
```

---

## 7. Known Issues / Follow-Ups

1. **Real policies unverified**: All 20 `HOSP-R###.json` have `verification_status="unverified"` and `key_fields` marked `UNVERIFIED`. PDFs must be opened and 6 fields verified with page/section refs.
2. **Scorer expects evidence_refs**: Person A's reader output must include `evidence_ref` for each required condition and tier.
3. **FPL year/region**: Engine uses `default_fpl_year` and `default_region` from policy; can be overridden in `evaluate_eligibility(policy, household, resolver, fpl_year=2025, region="alaska")`.

---

## 8. Git Commands to Stage & Push

```powershell
# Stage intended files (excludes .venv, caches, local settings, credentials)
git add billback/ tests/ data/ scripts/ PERSON_B_HANDOFF.md

# Verify staged (should NOT include .venv/, __pycache__/, .pytest_cache/, .claude/settings.local.json)
git status

# Commit
git commit -m "Person B: Eligibility engine + 20 synthetic policies + 20 real policies + scorer + tests

- Core EligibilityEngine with Decimal arithmetic, FPL thresholds, condition states
- 36 pytest tests covering all 10 required scenarios + 3 regression fixes
- 20 synthetic hospital policies, 10 households, 200-combination answer key
- Evaluation script: 200/200 combinations match
- PolicyScorer for Person A's reader JSON (completeness, validity, consistency, evidence)
- 20 real hospital policies across 13 states (all marked unverified pending PDF review)
- 10 independent household test cases with manual Decimal calculations
- Demo script with 5 scenarios
- Fixed rounding bug (threshold quantized before comparison) and evidence year/region bug"

# Push to person-b-eligibility branch
git push origin person-b-eligibility
```

---

**End of Handoff** — Person A can now run the checklist above and deliver reader JSON that scores 100/100.