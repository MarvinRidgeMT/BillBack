"""AI choice benchmark: the shipped AI bill reader (Method A) vs Tesseract OCR + regex (Method B).

Both methods read every bill in eval/data/bills/; fields are scored with eval/compare.py. Reports fields correct
overall and by photo condition, seconds per bill and estimated cost per bill (tokens x backend/pricing.py).

    .venv/bin/python -m eval.bench_bill_reader            # live: ~1 cent per bill for Method A
    .venv/bin/python -m eval.bench_bill_reader --only B   # baseline only (free)

Writes eval/results/bench_bill_reader.json. docs/RESULTS.md is built from it by eval/run_all.py.
"""

from __future__ import annotations

import argparse
import time
from typing import Any, Optional

from backend import pricing
from eval import compare
from eval.baselines import tesseract_extract
from eval.common import content_type, load_bill_truths, load_result, run_meta, save_result

CONDITIONS = ("clean", "angled", "crumpled", "dim", "blurry")
CONFIRM_THRESHOLD = 0.8


def _score(fields: dict[str, Any], truth: dict[str, Any]) -> dict[str, bool]:
    return {f: compare.compare_bill_field(f, fields.get(f), truth[f]) for f in compare.BILL_FIELDS}


def run_method_a(truth: dict[str, Any]) -> dict[str, Any]:
    from backend.bill_reader.reader import read_bill

    data = truth["path"].read_bytes()
    start = time.perf_counter()
    res = read_bill(data, content_type(truth["path"]))
    seconds = time.perf_counter() - start
    out = res.to_dict()
    # Score the code-normalized value where there is one (cents, ISO date): that is what the app uses.
    got = {f: (v["normalized"] if v.get("normalized") is not None else v["value"]) for f, v in out["fields"].items()}
    return {
        "fields": got,
        "confidence": {f: v["confidence"] for f, v in out["fields"].items()},
        "fields_to_confirm": out["fields_to_confirm"],
        "quality": out.get("quality"),
        "unreadable": out.get("unreadable"),
        "seconds": seconds,
        "input_tokens": res.input_tokens,
        "output_tokens": res.output_tokens,
        "cost_usd": pricing.estimate_cost_usd(res.model, res.input_tokens, res.output_tokens),
        "model": res.model,
    }


def run_method_b(truth: dict[str, Any]) -> dict[str, Any]:
    data = truth["path"].read_bytes()
    start = time.perf_counter()
    read = tesseract_extract.read_bill(data)
    return {"fields": read.fields, "method": read.method, "seconds": time.perf_counter() - start, "cost_usd": 0.0}


def _run(method: str, truth: dict[str, Any]) -> dict[str, Any]:
    try:
        row = run_method_a(truth) if method == "A" else run_method_b(truth)
    except tesseract_extract.OcrUnavailable as exc:
        return {"error": str(exc), "not_run": True}
    except Exception as exc:  # one failed bill must not hide the others; it scores 0/5 and is listed
        return {"error": f"{type(exc).__name__}: {exc}"}
    return {**row, "checks": _score(row["fields"], truth)}


def rescore(row: dict[str, Any], truth: Optional[dict[str, Any]]) -> dict[str, Any]:
    if truth is None or "fields" not in row:
        return row
    return {**row, "checks": _score(row["fields"], truth)}


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Totals for one method. Bills that errored count as 0/5; bills that were not run are left out."""
    ran = [r for r in rows if not r.get("not_run")]
    n_fields = len(compare.BILL_FIELDS)
    correct = sum(sum(r.get("checks", {}).values()) for r in ran)
    by_cond: dict[str, list[int]] = {}
    for r in ran:
        c = by_cond.setdefault(r["condition"], [0, 0])
        c[0] += sum(r.get("checks", {}).values())
        c[1] += n_fields
    timed = [r["seconds"] for r in ran if "seconds" in r]
    costs = [r["cost_usd"] for r in ran if r.get("cost_usd") is not None]
    low = sum(1 for r in ran for c in (r.get("confidence") or {}).values() if c < CONFIRM_THRESHOLD)
    # The dangerous kind of miss: a wrong value the patient is NOT asked to check.
    confident_wrong = sum(1 for r in ran for f, ok in r.get("checks", {}).items()
                          if not ok and f not in (r.get("fields_to_confirm") or []) and r.get("confidence") is not None)
    return {
        "bills_run": len(ran),
        "errors": sum(1 for r in ran if "error" in r),
        "correct": correct,
        "total": len(ran) * n_fields,
        "by_condition": {k: by_cond[k] for k in CONDITIONS if k in by_cond},
        "by_field": {f: sum(r.get("checks", {}).get(f, False) for r in ran) for f in compare.BILL_FIELDS},
        "avg_seconds": sum(timed) / len(timed) if timed else None,
        "max_seconds": max(timed) if timed else None,
        "avg_cost_usd": sum(costs) / len(costs) if costs else None,
        "low_confidence_fields": low,
        "fields_to_confirm": sum(len(r.get("fields_to_confirm") or []) for r in ran),
        "wrong_and_not_sent_to_patient": confident_wrong,
        # A wrong value is worse than a blank: the patient has nothing telling them to look.
        "wrong_values_returned": sum(1 for r in ran for f, ok in r.get("checks", {}).items()
                                     if not ok and (r.get("fields") or {}).get(f) is not None),
        "flagged_unreadable": [r["bill"] for r in ran if r.get("unreadable")],
        "flagged_poor_photo": [r["bill"] for r in ran if (r.get("quality") or {}).get("ok") is False],
    }


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--only", choices=("A", "B"), help="run one method; the other is kept from the last saved run")
    args = ap.parse_args(argv)
    previous = load_result("bench_bill_reader") or {}
    truths = load_bill_truths()
    by_name = {t["name"]: t for t in truths}
    methods: dict[str, list] = {"A": [], "B": []}
    metas: dict[str, dict] = {}
    for m in ("A", "B"):
        if args.only and args.only != m:
            kept = previous.get("methods", {}).get(m, {})
            # Re-score the saved reads with today's comparison rules (no model call); keep when they were read.
            methods[m] = [rescore(r, by_name.get(r["bill"])) for r in kept.get("rows", [])]
            metas[m] = kept.get("meta") or {k: previous.get(k) for k in ("generated_at", "model", "git_commit")}
            continue
        metas[m] = run_meta()
        for t in truths:
            row = {"bill": t["name"], "condition": t["condition"], **_run(m, t)}
            methods[m].append(row)
            status = row.get("error") or f"{sum(row['checks'].values())}/5  {row['seconds']:.1f}s"
            print(f"[{m}] {t['name']:24} {t['condition']:9} {status}")
    payload = run_meta(
        method_a="AI bill reader shipped in the app (backend/bill_reader/reader.py)",
        method_b="Tesseract OCR + regex/heuristics (eval/baselines/tesseract_extract.py)",
        rules=compare.RULES_TEXT,
        pricing_source=pricing.PRICING_SOURCE,
        methods={m: {"summary": summarize(rows), "rows": rows, "meta": metas[m]} for m, rows in methods.items()},
    )
    save_result("bench_bill_reader", payload)
    for m in ("A", "B"):
        s = payload["methods"][m]["summary"]
        print(f"Method {m}: {s['correct']}/{s['total']} fields, avg {s['avg_seconds']} s, avg ${s['avg_cost_usd']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
