"""Repeatability: the same input through the pipeline N times. Fresh model calls every time (no cache, nothing saved).

- 3 bills x N runs: are the 5 extracted values (code-normalized) identical? (confidence spread reported separately)
- 3 policies x N runs: are the rules identical? Checked two ways: the decision values the engine uses
  (free %, discount %, tiers, asset test, residency, window days, statuses) and the full rules JSON
- eligibility on each run's rules for 3 fixed households: identical results?
Anything that differs is listed field by field.

    .venv/bin/python -m eval.repeat_runs [--runs 5]     (live: ~$0.90 for 5 runs with Claude Sonnet 5.5)
Writes eval/results/repeat_runs.json.
"""

from __future__ import annotations

import argparse
import json
import time
from typing import Any, Optional

from backend import fpl, pricing
from backend.bill_reader.reader import read_bill
from backend.eligibility import load_fpl_table_from_json, run_eligibility
from backend.policy_reader.reader import read_policy
from backend.policy_reader.schema import EVIDENCE_FIELDS, PolicyRules
from eval.common import REPO, content_type, load_bill_truths, load_result, run_meta, save_result

BILLS = ("bill_01_clean", "bill_05_crumpled", "bill_10_crumpled_dim")
POLICIES = {  # short, medium and table-heavy policies from data/policies
    "fort-healthcare-inc": "fort-healthcare-wi.pdf",
    "usa-health": "usa-health-al.pdf",
    "marshfield-clinic-health-system": "marshfield-clinic-wi.pdf",
}
HOUSEHOLDS = ({"size": 2, "income": 30000, "assets": 0}, {"size": 4, "income": 90000, "assets": 0},
              {"size": 3, "income": 150000, "assets": 0})
VOLATILE = ("source",)  # retrieval metadata, not extracted content


def decision_values(rules: PolicyRules) -> dict[str, Any]:
    """What the rules engine actually uses."""
    return {
        "free_care.fpl_max_percent": rules.free_care.fpl_max_percent,
        "discount.fpl_max_percent": rules.discount.fpl_max_percent,
        "discount.tiers": [(t.fpl_min_percent, t.fpl_max_percent, t.discount_type, t.value) for t in rules.discount.tiers],
        "asset_test.applies": rules.asset_test.applies,
        "residency.required": rules.residency.required,
        "application_window.days": rules.application_window.days,
        **{f"{f}.status": getattr(rules, f).evidence.status for f in EVIDENCE_FIELDS},
        "review_fields": sorted(rules.review_fields),
        "income_basis": rules.income_basis,
    }


def _differences(runs: list[dict[str, Any]]) -> dict[str, list[Any]]:
    """key -> the distinct values seen across runs (only keys that changed)."""
    out = {}
    for key in runs[0]:
        seen = []
        for r in runs:
            if r.get(key) not in seen:
                seen.append(r.get(key))
        if len(seen) > 1:
            out[key] = seen
    return out


def repeat_bills(n: int) -> list[dict[str, Any]]:
    truths = {t["name"]: t for t in load_bill_truths()}
    out = []
    for name in BILLS:
        t = truths[name]
        data, ctype = t["path"].read_bytes(), content_type(t["path"])
        runs, confs, costs = [], [], []
        for _ in range(n):
            res = read_bill(data, ctype).to_dict()
            runs.append({f: (v["normalized"] if v.get("normalized") is not None else v["value"]) for f, v in res["fields"].items()})
            confs.append({f: v["confidence"] for f, v in res["fields"].items()})
        diffs = _differences(runs)
        spread = {f: [min(c[f] for c in confs), max(c[f] for c in confs)] for f in confs[0]}
        out.append({"bill": name, "runs": n, "identical_runs": sum(r == runs[0] for r in runs),
                    "all_identical": not diffs, "differences": diffs, "confidence_range": spread})
        print(f"bill {name}: {'identical' if not diffs else diffs}")
    return out


def _eligibility(rules: PolicyRules, state: str, resolver, year: int) -> list[str]:
    return [run_eligibility(rules, h["size"], h["income"], state, resolver, year, assets_usd=h["assets"]).status.value
            for h in HOUSEHOLDS]


def repeat_policies(n: int) -> list[dict[str, Any]]:
    table = fpl.load_table()
    resolver, year = load_fpl_table_from_json(table), int(table["year"])
    out = []
    for slug, pdf_name in POLICIES.items():
        pdf = (REPO / "data" / "policies" / pdf_name).read_bytes()
        decisions, full, elig, secs, costs = [], [], [], [], []
        for _ in range(n):
            start = time.perf_counter()
            res = read_policy(pdf, use_cache=False, persist=False)  # fresh model call, nothing written
            secs.append(time.perf_counter() - start)
            costs.append(res.estimated_cost_usd())
            decisions.append(decision_values(res.rules))
            full.append(json.dumps(res.rules.model_dump(mode="json", exclude=set(VOLATILE)), sort_keys=True))
            elig.append({f"household_{i + 1}": s for i, s in enumerate(_eligibility(res.rules, res.rules.hospital_state or "WI", resolver, year))})
        d_diff, e_diff = _differences(decisions), _differences(elig)
        out.append({
            "policy": slug, "runs": n,
            "decision_values_identical_runs": sum(d == decisions[0] for d in decisions),
            "full_json_identical_runs": sum(f == full[0] for f in full),
            "eligibility_identical_runs": sum(e == elig[0] for e in elig),
            "decision_differences": d_diff, "eligibility_differences": e_diff,
            "eligibility_first_run": elig[0],
            "avg_seconds": sum(secs) / len(secs), "avg_cost_usd": sum(c or 0 for c in costs) / len(costs),
        })
        print(f"policy {slug}: decisions {out[-1]['decision_values_identical_runs']}/{n} same, full JSON "
              f"{out[-1]['full_json_identical_runs']}/{n}, eligibility {out[-1]['eligibility_identical_runs']}/{n}; {d_diff or ''}")
    return out


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--runs", type=int, default=5)
    ap.add_argument("--only", choices=("bills", "policies"))
    args = ap.parse_args(argv)
    previous = load_result("repeat_runs") or {}
    now = run_meta()["generated_at"]
    if args.only == "policies":  # keep the other half from the last run, with its own timestamp
        bills, bills_at = previous.get("bills", []), previous.get("bills_generated_at", previous.get("generated_at"))
    else:
        bills, bills_at = repeat_bills(args.runs), now
    if args.only == "bills":
        pols, pols_at = previous.get("policies", []), previous.get("policies_generated_at", previous.get("generated_at"))
    else:
        pols, pols_at = repeat_policies(args.runs), now
    save_result("repeat_runs", run_meta(runs=args.runs, bills=bills, policies=pols, households=HOUSEHOLDS,
                                        bills_generated_at=bills_at, policies_generated_at=pols_at,
                                        pricing_source=pricing.PRICING_SOURCE,
                                        determinism_note="Claude Sonnet 5.5 rejects temperature/seed; JSON schema output on every call."))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
