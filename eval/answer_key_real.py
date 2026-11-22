"""B's hand-check of the policy reader on 6 real policies (36 fields).

    python -m eval.answer_key_real --make     # writes eval/answer_key_real_TODO.csv (correct_value / is_correct BLANK)
    python -m eval.answer_key_real            # scores it once B has filled it in

B fills `correct_value` from the PDF and `is_correct` (yes/no) for each row. We never fill those columns.
`score()` returns None until every row has `is_correct`, so a half-filled key is never reported as a result.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Optional

from backend.policy_reader.cache import DEFAULT_CACHE_DIR, REPO_ROOT
from backend.policy_reader.schema import PolicyRules

CSV_PATH = REPO_ROOT / "eval" / "answer_key_real_TODO.csv"
COLUMNS = ["policy_id", "hospital", "field", "reader_value", "reader_quote", "page", "pdf_url", "correct_value", "is_correct"]
POLICIES = [  # (B's id, cached policy slug)
    ("HOSP-R003", "baptist-health-south-florida"),
    ("HOSP-R007", "texas-health-resources-texas-health"),
    ("HOSP-R009", "uw-medicine-harborview-medical-center-uw-medical-center-airl"),
    ("HOSP-R010", "uchealth"),
    ("HOSP-R012", "emory-healthcare"),
    ("HOSP-R013", "banner-health"),
]
YES = {"yes", "y", "true", "1", "correct"}
NO = {"no", "n", "false", "0", "wrong", "incorrect"}


def _load(slug: str) -> PolicyRules:
    path = next(Path(DEFAULT_CACHE_DIR).glob(f"{slug}__*.json"))
    return PolicyRules.model_validate_json(path.read_text())


def _tiers(rules: PolicyRules) -> str:
    parts = []
    for t in rules.discount.tiers:
        value = "" if t.value is None else f" {t.value:g}"
        parts.append(f"{t.fpl_min_percent or 0:g}-{t.fpl_max_percent if t.fpl_max_percent is not None else '?'}%: {t.discount_type}{value}")
    return "; ".join(parts) or "none"


def _fields(rules: PolicyRules) -> list[tuple[str, str, Any]]:
    """(field label, reader value as text, evidence) for the 6 answer-key fields."""
    w = rules.application_window
    return [
        ("free_care %", "not stated" if rules.free_care.fpl_max_percent is None else f"{rules.free_care.fpl_max_percent:g}", rules.free_care.evidence),
        ("discount max %", "not stated" if rules.discount.fpl_max_percent is None else f"{rules.discount.fpl_max_percent:g}", rules.discount.evidence),
        ("discount tiers", _tiers(rules), rules.discount.evidence),
        ("asset test", f"{rules.asset_test.applies}" + (f" ({rules.asset_test.details})" if rules.asset_test.details else ""), rules.asset_test.evidence),
        ("residency", f"{rules.residency.required}" + (f" ({rules.residency.area})" if rules.residency.area else ""), rules.residency.evidence),
        ("application window", "not stated" if w.days is None else f"{w.days} days from {w.counted_from}", w.evidence),
    ]


def make() -> None:
    rows = []
    for pid, slug in POLICIES:
        rules = _load(slug)
        url = rules.source.url if rules.source else ""
        for label, value, ev in _fields(rules):
            rows.append({"policy_id": pid, "hospital": rules.hospital_name, "field": label, "reader_value": value,
                         "reader_quote": ev.quote or "", "page": ev.page or "", "pdf_url": url or "",
                         "correct_value": "", "is_correct": ""})
    with CSV_PATH.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {CSV_PATH} ({len(rows)} rows; correct_value and is_correct left blank for B)")


def score(path: Path = CSV_PATH) -> Optional[dict[str, Any]]:
    """{'correct': n, 'total': m, 'by_field': {...}} once every row has is_correct; otherwise None."""
    if not path.exists():
        return None
    with path.open() as fh:
        rows = list(csv.DictReader(fh))
    marks = [r.get("is_correct", "").strip().lower() for r in rows]
    if not rows or any(m not in YES | NO for m in marks):
        return None
    by_field: dict[str, list[int]] = {}
    for r, m in zip(rows, marks):
        by_field.setdefault(r["field"], [0, 0])
        by_field[r["field"]][0] += int(m in YES)
        by_field[r["field"]][1] += 1
    return {"correct": sum(m in YES for m in marks), "total": len(rows), "by_field": by_field}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--make", action="store_true", help="write the TODO CSV from the cached reads")
    if parser.parse_args().make:
        make()
        return 0
    result = score()
    print(json.dumps(result, indent=2) if result else "answer key not filled in yet (is_correct is blank on some rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
