"""One command for every number: runs each eval and writes docs/RESULTS.md + eval/results/*.json.

    python eval/run_all.py              # full run: live model calls (~$1.10 with Claude Sonnet 5.5) + free evals
    python eval/run_all.py --offline    # no model calls: re-scores saved runs, re-runs everything that is free
    python eval/run_all.py --runs 3     # fewer repeat runs

Needs ANTHROPIC_API_KEY in .env for live steps, and the `tesseract` binary for the OCR baseline
(brew install tesseract). A step that can't run is reported as "not run" with the reason; nothing is invented.
"""

from __future__ import annotations

import argparse
import csv
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:  # allow `python eval/run_all.py` from a clean clone
    sys.path.insert(0, str(REPO))

from eval import compare  # noqa: E402
from eval.common import RESULTS, load_result, run_meta, save_result  # noqa: E402

RESULTS_MD = REPO / "docs" / "RESULTS.md"
MANUAL_TIMING = REPO / "eval" / "manual_timing.csv"
TODO = "TODO(team)"


# ---------------------------------------------------------------- running the steps

def _step(name: str, fn, *args) -> Optional[str]:
    print(f"\n=== {name} ===", flush=True)
    try:
        fn(*args)
        return None
    except Exception as exc:  # one broken step must not hide the others; it's reported in RESULTS.md
        print(f"{name} FAILED: {type(exc).__name__}: {exc}")
        return f"{type(exc).__name__}: {exc}"


def run_pytest() -> dict[str, Any]:
    proc = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"], cwd=REPO,
                          capture_output=True, text=True)
    last = proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else ""
    counts = {k: int(v) for v, k in re.findall(r"(\d+) (passed|failed|skipped|errors?)", last)}
    summary = run_meta(line=last, returncode=proc.returncode, **counts)
    save_result("pytest", summary)
    print(last)
    return summary


def run_steps(offline: bool, runs: int) -> dict[str, Optional[str]]:
    from eval import bench_bill_reader, live_mode_check, policy_grounding, repeat_runs, run_households

    errors: dict[str, Optional[str]] = {}
    errors["pytest"] = _step("pytest", run_pytest)
    if offline:
        errors["bench"] = _step("bill reader benchmark (Method B only; Method A kept from the last live run)",
                                bench_bill_reader.main, ["--only", "B"])
    else:
        errors["bench"] = _step("bill reader benchmark", bench_bill_reader.main, [])
        errors["repeat"] = _step("repeat runs", repeat_runs.main, ["--runs", str(runs)])
    errors["grounding"] = _step("policy grounding + accuracy", policy_grounding.main, [])
    errors["households"] = _step("households end to end", run_households.main, [])
    if load_result("live_mode_check") is None:
        errors["live_mode"] = _step("live mode check", live_mode_check.main, [])
    return errors


# ---------------------------------------------------------------- formatting helpers

def pct(n: Optional[float], d: Optional[float]) -> str:
    return f"{100 * n / d:.0f}%" if n is not None and d else "—"


def frac(n: Optional[int], d: Optional[int]) -> str:
    return f"{n}/{d} ({pct(n, d)})" if d else "not run"


def money(x: Optional[float], places: int = 4) -> str:
    return f"${x:.{places}f}" if x is not None else "—"


def secs(x: Optional[float]) -> str:
    return f"{x:.1f} s" if x is not None else "—"


def stamp(res: Optional[dict[str, Any]]) -> str:
    if not res:
        return "_not run yet_"
    return f"_Run {res.get('generated_at', '?')}, model `{res.get('model', '?')}`, commit `{res.get('git_commit', '?')}`._"


# ---------------------------------------------------------------- sections

def bill_section(bench: Optional[dict[str, Any]]) -> tuple[list[str], dict[str, Any]]:
    lines = ["## 1. Bill reader: AI vs. OCR baseline (rubric A1)", ""]
    if not bench:
        return lines + ["Not run yet: `python -m eval.bench_bill_reader`.", ""], {}
    a, b = bench["methods"]["A"]["summary"], bench["methods"]["B"]["summary"]
    b_rows = bench["methods"]["B"]["rows"]
    b_missing = sum(1 for r in b_rows if r.get("not_run"))
    meta_a, meta_b = bench["methods"]["A"].get("meta"), bench["methods"]["B"].get("meta")
    lines += [f"Method A read the bills: {stamp(meta_a or bench)[1:-1]}. Method B: {stamp(meta_b or bench)[1:-1]}. "
              "Scores below use today's comparison rules.", "",
              f"Method A: {bench['method_a']}. Method B: {bench['method_b']}. Same {a['bills_run'] or len(b_rows)} bills, "
              "same scoring rules (section 8).", ""]
    if b_missing:
        lines += [f"> **Method B ran on {b['bills_run']} of {len(b_rows)} bills**: the `tesseract` binary was not installed "
                  "on the machine that produced this file, so only the text PDFs (no OCR needed) were scored. "
                  f"{TODO}: install Tesseract (`brew install tesseract poppler`) and run `python eval/run_all.py` again.", ""]
    lines += ["| | Method A (AI) | Method B (Tesseract + regex) |", "|---|---|---|",
              f"| Bills scored | {a['bills_run']} | {b['bills_run']} |",
              f"| Fields correct, bills scored | **{frac(a['correct'], a['total'])}** | {frac(b['correct'], b['total'])} |"]
    for cond in ("clean", "angled", "crumpled", "dim", "blurry"):
        ca, cb = a["by_condition"].get(cond), b["by_condition"].get(cond)
        if ca or cb:
            lines.append(f"| {cond} | {frac(*(ca or [None, None]))} | {frac(*(cb or [None, None]))} |")
    lines += [f"| Average seconds per bill | {secs(a['avg_seconds'])} | {secs(b['avg_seconds'])} |",
              f"| Estimated cost per bill | {money(a['avg_cost_usd'])} | $0 (runs locally) |",
              "| (time and cost leave out bills that errored) | | |",
              f"| Bills that errored | {a['errors']} | {b['errors']} |",
              f"| Wrong values NOT sent to the patient to check | **{a.get('wrong_and_not_sent_to_patient', '—')}** | n/a (no confidence scores) |", "",
              f"Image-quality check (plain code): flagged as poor photos {', '.join(a.get('flagged_poor_photo') or []) or 'none'}; "
              f"flagged as unreadable (patient offered *Retake* or *Enter by hand*, pre-filled) {', '.join(a.get('flagged_unreadable') or []) or 'none'}.", "",
              "| Field | Method A | Method B |", "|---|---|---|",
              *[f"| {f} | {a['by_field'][f]}/{a['bills_run']} | {b['by_field'][f]}/{b['bills_run']} |" for f in compare.BILL_FIELDS], "",
              f"Cost = tokens × the published price in `backend/pricing.py` ({bench.get('pricing_source', '')}). "
              "Condition = the hardest condition on the bill (blurry > dim > crumpled > angled > clean); text PDFs count as clean.", ""]
    misses = [(m, r["bill"], f) for m in ("A", "B") for r in bench["methods"][m]["rows"] if not r.get("not_run")
              for f, ok in r.get("checks", {}).items() if not ok]
    if misses:
        lines += ["Every miss: " + "; ".join(f"{m}: {bill} {field}" for m, bill, field in misses) + ".", ""]
    same = _same_bills(bench)
    if b_missing and same["bills"]:
        lines += [f"On the {same['bills']} bills both methods ran: AI {frac(same['a'], same['total'])}, "
                  f"baseline {frac(same['b'], same['total'])}.", ""]
    full = not b_missing
    gap = (a["correct"] / a["total"] - b["correct"] / b["total"]) * 100 if full and a["total"] and b["total"] else None
    lines += ["### Why Claude Sonnet 5.5 for reading bills (draft for the team to finalize)", "",
              f"> On our {a['bills_run']} test bills, the AI reader got {frac(a['correct'], a['total'])} of fields right"
              + (f", against {frac(b['correct'], b['total'])} for a Tesseract-plus-rules baseline ({gap:+.0f} points)" if gap is not None else "")
              + f", at about {money(a['avg_cost_usd'], 3)} and {secs(a['avg_seconds'])} per bill. "
              + ("Where the gap shows on the photos patients actually take (angled, crumpled, dim, blurry) is in the "
                 "condition table above. " if gap is not None else
                 f"The OCR baseline hasn't been run on photos yet ({TODO}, see the note above), so we make no claim "
                 "about how much better the AI does on them until it has. ")
              + "The AI also returns a confidence for each field, which is what lets BillBack send unsure fields back "
              f"to the patient instead of guessing: wrong values not sent to the patient to check: "
              f"{a.get('wrong_and_not_sent_to_patient', '—')}. {TODO}: finalize the wording against the latest run.", ""]
    return lines, {"a": a, "b": b, "same": same, "b_complete": full}


def _same_bills(bench: dict[str, Any]) -> dict[str, int]:
    """Both methods scored only on bills both of them actually ran (fair comparison when OCR was missing)."""
    rows_a = {r["bill"]: r for r in bench["methods"]["A"]["rows"] if not r.get("not_run") and "checks" in r}
    rows_b = {r["bill"]: r for r in bench["methods"]["B"]["rows"] if not r.get("not_run") and "checks" in r}
    both = sorted(set(rows_a) & set(rows_b))
    return {"bills": len(both), "total": 5 * len(both),
            "a": sum(sum(rows_a[x]["checks"].values()) for x in both),
            "b": sum(sum(rows_b[x]["checks"].values()) for x in both)}


def policy_section(g: Optional[dict[str, Any]]) -> list[str]:
    lines = ["## 2. Policy reader: accuracy and the grounding check (rubric A2, A3)", ""]
    if not g:
        return lines + ["Not run yet: `python -m eval.policy_grounding`.", ""]
    f, acc = g["flags"], g["accuracy"]
    lines += [stamp(g), ""]
    if acc["status"] == "pending":
        lines += [f"**Policy fields correct: pending, 0 of {acc['target_fields']} scored.** The answer key "
                  f"(`eval/verify/answer_key.csv`, {acc['key_rows']} rows for the 17 readable policies) has no rows verified by "
                  f"a person yet, and we don't fill it from model output. {TODO} (B): verify the rows, then re-run.", "",
                  "**Precision of the grounding check: pending** (needs the same verified rows).", ""]
    else:
        lines += [f"**Policy fields correct: {acc['correct']} of {acc['verified_rows']} verified fields** "
                  f"({pct(acc['correct'], acc['verified_rows'])}) across {acc['policies_scored']} policies "
                  f"(target set: {acc['target_fields']} fields).", "",
                  f"**Grounding check precision:** of {acc['flagged_rows']} verified fields the check flagged, "
                  f"{acc['flagged_and_wrong']} were actually wrong ({pct(acc['flagged_and_wrong'], acc['flagged_rows'])}). "
                  f"It caught {acc['wrong_and_flagged']} of {acc['wrong_rows']} wrong fields.", ""]
    reasons = f["flag_reasons"]
    lines += ["What the plain-code checks did on every cached real policy (no model call):", "",
              "| | Count |", "|---|---|",
              f"| Policies | {f['policies']} |",
              f"| Fields (5 rule groups per policy; the 6 answer-key fields fold discount limit + amount into one) | {f['fields']} |",
              f"| Stated fields whose quote was found word for word (normalized, or fuzzy ≥ 0.90) in the PDF | {f['quotes_verified']}/{f['stated']} |",
              f"| Fields flagged “needs checking” | {f['flagged']}/{f['fields']} |",
              *[f"| …because: {k.replace('_', ' ')} | {v} |" for k, v in sorted(reasons.items())], "",
              "A flagged field is never used silently: its confidence is capped, the patient sees “needs checking”, and "
              "an unclear residency or savings rule makes the result “we can't tell” instead of a pass.", ""]
    return lines


def repeat_section(rep: Optional[dict[str, Any]]) -> list[str]:
    lines = ["## 3. Repeatability (rubric R2)", ""]
    if not rep:
        return lines + ["Not run yet: `python -m eval.repeat_runs`.", ""]
    n = rep["runs"]
    lines += [stamp(rep), f"_Bills run {rep.get('bills_generated_at', '?')}; policies run {rep.get('policies_generated_at', '?')}._", "",
              f"Same input, {n} fresh model calls each (no cache). {rep['determinism_note']}", "",
              "| Input | Identical extracted values | Identical rules (decision values) | Identical full rules JSON | Identical eligibility (3 households) |",
              "|---|---|---|---|---|"]
    for b in rep["bills"]:
        lines.append(f"| Bill {b['bill']} | {b['identical_runs']}/{n} | — | — | — |")
    for p in rep["policies"]:
        lines.append(f"| Policy {p['policy']} | — | {p['decision_values_identical_runs']}/{n} | {p['full_json_identical_runs']}/{n} | "
                     f"{p['eligibility_identical_runs']}/{n} |")
    diffs = [(f"bill {b['bill']}", k, v) for b in rep["bills"] for k, v in b["differences"].items()] + \
            [(f"policy {p['policy']}", k, v) for p in rep["policies"] for k, v in {**p["decision_differences"], **p["eligibility_differences"]}.items()]
    lines += ["", "What differed between runs:" if diffs else "Nothing that the app uses differed between runs.", ""]
    lines += [f"- {where}: `{key}` took {len(vals)} values: {', '.join(f'`{v}`' for v in vals)}" for where, key, vals in diffs]
    lines += ["", "Full-JSON differences are wording (quotes, tier descriptions, warnings); the table above separates them "
              "from the values the rules engine uses.", ""]
    before = rep.get("policies_before_prompt_fix")
    if before:
        lines += ["### Before and after fixing the prompt", "",
                  f"The first policy run ({rep.get('policies_before_prompt_fix_generated_at', '?')}) disagreed with itself, so we fixed "
                  "the cause, not the number: the prompt had no rule for conditional requirements (Marshfield's residency rule is "
                  "waived for emergencies), for asset words outside an asset section, or for when to merge discount bands. Three "
                  "rules were added to `backend/prompts/policy_reader.md` and the policies were run again.", "",
                  "| Policy | Decision values identical, before → after | Eligibility identical, before → after |", "|---|---|---|"]
        after = {p["policy"]: p for p in rep["policies"]}
        for b in before:
            a = after.get(b["policy"], {})
            lines.append(f"| {b['policy']} | {b['decision_values_identical_runs']}/{n} → {a.get('decision_values_identical_runs', '—')}/{n} | "
                         f"{b['eligibility_identical_runs']}/{n} → {a.get('eligibility_identical_runs', '—')}/{n} |")
        lines += ["", "Before the fix: " + "; ".join(
            f"{b['policy']} `{k}` took values {', '.join(f'`{v}`' for v in vals)}"
            for b in before for k, vals in {**b["decision_differences"], **b["eligibility_differences"]}.items()) + ".", ""]
    return lines


def households_section(hh: Optional[dict[str, Any]]) -> list[str]:
    lines = ["## 4. End to end: 10 households (rubric R2, A3)", ""]
    if not hh:
        return lines + ["Not run yet: `python -m eval.run_households`.", ""]
    sources = hh.get("bill_sources") or {}
    how = ", ".join(f"{n} {k}" for k, n in sources.items()) or "saved reads"
    lines += [stamp(hh), "", f"**{hh['correct']}/{hh['total']} households correct** through the real pipeline: sample-bill "
              f"read ({how}) → hospital match → cached real policy → rules engine → application PDF. Expected results: "
              f"{hh['expectations_by']}; checked by: {hh['checked_by']}.", "",
              "| Household | Hospital | % of poverty line | Expected | Got | Correct |", "|---|---|---|---|---|---|"]
    for r in hh["rows"]:
        lines.append(f"| {r['id']} | {r['matched_slug']} | {r['percent_of_fpl']}% | {r['expected_status']} | {r['status']} | "
                     f"{'✅' if r['correct'] else '❌'} |")
    misses = [r for r in hh["rows"] if not r["correct"]]
    if misses:
        lines += ["", "Mismatches (kept, not hidden):", ""]
        lines += [f"- **{r['id']}**: expected `{r['expected_status']}`, engine said `{r['status']}`. {r['explanation']}" for r in misses]
    if hh.get("b_hand_key"):
        k = hh["b_hand_key"]
        lines += ["", f"B's hand-calculated key (10 households × 20 synthetic policies, 2026 table): "
                  f"{k['households_status_ok_2026']}/{k['households']} households and {k['status_ok_2026']}/{k['n']} results match on status."]
    return lines + [""]


def _manual_rows() -> list[dict[str, str]]:
    if not MANUAL_TIMING.exists():
        return []
    return list(csv.DictReader(MANUAL_TIMING.open(newline="")))


def timing_section(bench_stats: dict[str, Any], rep: Optional[dict[str, Any]], hh: Optional[dict[str, Any]]) -> list[str]:
    lines = ["## 5. Speed and cost (rubric V2)", ""]
    a = bench_stats.get("a") or {}
    policy_secs = [p["avg_seconds"] for p in (rep or {}).get("policies", [])]
    policy_cost = [p["avg_cost_usd"] for p in (rep or {}).get("policies", [])]
    avg_policy = sum(policy_secs) / len(policy_secs) if policy_secs else None
    lines += ["| Step | Average | Source |", "|---|---|---|",
              f"| Bill read (AI) | {secs(a.get('avg_seconds'))}, {money(a.get('avg_cost_usd'))} | bill benchmark, Method A |",
              f"| Policy read, first time a hospital is seen (AI) | {secs(avg_policy)}, "
              f"{money(sum(policy_cost) / len(policy_cost) if policy_cost else None)} | repeat runs (3 policies × {(rep or {}).get('runs', '—')}) |",
              "| Policy read, cached hospital | ~0 s, $0 | cache lookup, no model call |",
              f"| Rules engine + packet, per household | {secs(sum(r['seconds'] for r in hh['rows']) / len(hh['rows']) if hh else None)} (incl. match) | households end to end |",
              "", "The app also logs these per step in memory and shows them on the dev panel (`?dev=1`).", ""]
    rows = _manual_rows()
    filled = [r for r in rows if r["minutes_to_find_6_fields"] and TODO not in r["minutes_to_find_6_fields"]]
    lines += ["### A person vs. BillBack, finding the 6 fields in a policy", ""]
    if not filled:
        lines += [f"Pending: {TODO} fill in `eval/manual_timing.csv` (time yourself finding the 6 fields in 3 policies); "
                  "this table fills itself in on the next run.", ""]
    else:
        lines += ["| Policy | Person | Person (minutes) | BillBack policy read (seconds) |", "|---|---|---|---|"]
        lines += [f"| {r['policy']} | {r['reader']} | {r['minutes_to_find_6_fields']} | {secs(avg_policy)} |" for r in filled]
        lines.append("")
    return lines


def low_conf_section(bench_stats: dict[str, Any]) -> list[str]:
    a = bench_stats.get("a")
    if not a:
        return []
    total = a["total"]
    return ["## 6. Fields sent back to the patient", "",
            f"Bill fields under 0.8 confidence: {a['low_confidence_fields']}/{total}; fields the app asked the patient to "
            f"confirm (low confidence or failed a code check): {a['fields_to_confirm']}/{total}. The app counts this per session "
            "in memory (dev panel) and stores nothing.", ""]


def tests_section(pt: Optional[dict[str, Any]]) -> list[str]:
    if not pt:
        return []
    return ["## 7. Tests", "", f"`pytest`: {pt.get('line', '')} ({stamp(pt)[1:-1]}).", ""]


def summary_table(bench_stats, g, rep, hh, pt) -> list[str]:
    a, b = bench_stats.get("a"), bench_stats.get("b")
    rows = []
    if a and b and bench_stats.get("b_complete"):
        rows.append(("Bill fields correct, AI vs. Tesseract baseline", f"{frac(a['correct'], a['total'])} vs. {frac(b['correct'], b['total'])}"))
    elif a and b:
        same = bench_stats["same"]
        rows.append(("Bill fields correct (AI), all bills", frac(a["correct"], a["total"])))
        rows.append(("AI vs. Tesseract baseline", f"baseline incomplete (Tesseract not installed): on the {same['bills']} text-PDF "
                     f"bills both ran, {frac(same['a'], same['total'])} vs. {frac(same['b'], same['total'])}"))
        rows.append(("Time and cost per bill (AI)", f"{secs(a['avg_seconds'])}, {money(a['avg_cost_usd'])}"))
    if g:
        acc = g["accuracy"]
        rows.append(("Policy fields correct (of 120)", "pending (no person-verified key yet)" if acc["status"] == "pending"
                     else f"{acc['correct']}/{acc['verified_rows']} verified"))
        rows.append(("Policy quotes found word for word in the PDF", f"{g['flags']['quotes_verified']}/{g['flags']['stated']}"))
        rows.append(("Policy fields flagged “needs checking”", f"{g['flags']['flagged']}/{g['flags']['fields']} (precision: "
                     + ("pending" if acc["status"] == "pending" else pct(acc["flagged_and_wrong"], acc["flagged_rows"])) + ")"))
    if rep:
        n = rep["runs"]
        same_bills = sum(b_["all_identical"] for b_ in rep["bills"])
        same_rules = sum(p["decision_values_identical_runs"] == n for p in rep["policies"])
        same_elig = sum(p["eligibility_identical_runs"] == n for p in rep["policies"])
        rows.append((f"Repeat runs ({n}×): bills / policy decision values / eligibility identical",
                     f"{same_bills}/{len(rep['bills'])} bills, {same_rules}/{len(rep['policies'])} policies, {same_elig}/{len(rep['policies'])} policies"))
    if hh:
        rows.append(("Households correct end to end", f"{hh['correct']}/{hh['total']}"))
    if pt:
        rows.append(("Tests", pt.get("line", "")))
    return ["| Measure | Result |", "|---|---|", *[f"| {k} | {v} |" for k, v in rows], ""]


def write_results(step_errors: dict[str, Optional[str]]) -> str:
    bench, g, rep = load_result("bench_bill_reader"), load_result("policy_grounding"), load_result("repeat_runs")
    hh, pt, live = load_result("households_e2e"), load_result("pytest"), load_result("live_mode_check")
    bill_lines, bench_stats = bill_section(bench)
    lines = ["# BillBack results", "",
             "Generated by `python eval/run_all.py` (do not edit by hand; edit the scripts in `eval/`). Every number comes "
             "from a script run recorded in `eval/results/*.json` with its time, model and commit. Bills and households are fictional.", "",
             *summary_table(bench_stats, g, rep, hh, pt),
             *bill_lines, *policy_section(g), *repeat_section(rep), *households_section(hh),
             *timing_section(bench_stats, rep, hh), *low_conf_section(bench_stats), *tests_section(pt),
             "## 8. How fields are compared", "", compare.RULES_TEXT + " (Code: `eval/compare.py`, tests: `backend/tests/test_compare.py`.)", "",
             "## 9. Live mode on hospitals we hadn't seen", ""]
    if live and live.get("rows"):
        lines += [stamp(live), "", "Extracted rules for a person to check: `eval/results/live_mode_check.csv`.", ""]
        lines += [f"- {r['url']}: {r.get('hospital') or 'error: ' + r.get('error', '')}" for r in live["rows"]]
    else:
        lines += [f"Pending: {TODO} add 2–3 policy links for hospitals not in our set to `eval/live_mode_check.py`, run it, "
                  "and fill in the hand-check column.", ""]
    failed = {k: v for k, v in step_errors.items() if v}
    if failed:
        lines += ["", "## Steps that failed on the last run", "", *[f"- {k}: {v}" for k, v in failed.items()]]
    RESULTS_MD.write_text("\n".join(lines) + "\n")
    return RESULTS_MD.as_posix()


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--offline", action="store_true", help="no model calls; reuse saved live runs")
    ap.add_argument("--runs", type=int, default=5, help="repeat runs per input")
    ap.add_argument("--report-only", action="store_true", help="only rebuild docs/RESULTS.md from saved results")
    args = ap.parse_args(argv)
    errors = {} if args.report_only else run_steps(args.offline, args.runs)
    print(f"\nwrote {write_results(errors)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
