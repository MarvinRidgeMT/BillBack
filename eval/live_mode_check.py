"""Live mode on hospitals NOT in the curated set: read each policy link the way the app does (memory only, nothing
cached) and print the extracted rules next to a blank column for a person to fill in by reading the PDF.

    .venv/bin/python -m eval.live_mode_check URL [URL ...]
    .venv/bin/python -m eval.live_mode_check            # uses UNSEEN_POLICY_URLS below

Writes eval/results/live_mode_check.json and eval/results/live_mode_check.csv (columns `hand_check_value`,
`reader_right` and `checked_by` are left blank for the team).
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from typing import Any, Optional

from backend import policies
from backend.errors import CODES
from backend.policy_reader import grounding
from backend.policy_reader.extract_text import DocumentError
from backend.policy_reader.fetch import FetchError, fetch_policy
from backend.policy_reader.llm_clients import PolicyReaderError
from backend.policy_reader.reader import read_policy, read_policy_text
from eval.common import RESULTS, run_meta, save_result

# Hospitals NOT in cache/policies (the script refuses curated ones). Mad River was found with a web search on
# 2026-11-23 and also run through the app by hand. TODO(team, A): add 1-2 more, at least one a web page, not a PDF.
UNSEEN_POLICY_URLS: list[str] = [
    "http://madriverhospital.com/wp-content/uploads/2026/11/Financial_Assistance_Charity_Care_CLEAN.pdf",
]


def _value_text(value: Any) -> str:
    if isinstance(value, dict) and "tiers" in value:
        tiers = "; ".join(f"{t['fpl_min_percent']}-{t['fpl_max_percent']}%: {t['discount_type']} {t['value'] or ''}".strip()
                          for t in value["tiers"])
        return f"max {value['fpl_max_percent']}% [{tiers}]"
    if isinstance(value, dict):
        return ", ".join(f"{k}={v}" for k, v in value.items() if v is not None) or "not stated"
    return "not stated" if value is None else str(value)


def check(url: str) -> dict[str, Any]:
    if policies.curated_slug_for_url(url):
        return {"url": url, "error": "this policy is already in the curated set; pick an unseen hospital"}
    start = time.perf_counter()
    try:
        got = fetch_policy(url)
        result = read_policy(got.pdf_bytes, url=got.url, persist=False) if got.kind == "pdf" else read_policy_text(got.text, url=got.url)
    except (FetchError, DocumentError) as exc:
        return {"url": url, "error": str(exc), "code": exc.code}
    except PolicyReaderError as exc:
        return {"url": url, "error": str(exc), "code": "ai_unavailable"}
    view = grounding.grounded_view(result.rules)
    return {
        "url": url, "kind": got.kind, "hospital": result.rules.hospital_name, "state": result.rules.hospital_state,
        "seconds": time.perf_counter() - start, "cost_usd": result.estimated_cost_usd(),
        "fields": {k: {"value": _value_text(v["value"]), "page": v["page"], "confidence": v["confidence"],
                       "verified": v["verified"], "needs_checking": v["needs_checking"], "problems": v["problems"],
                       "source_quote": v["source_quote"]} for k, v in view.items()},
    }


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("urls", nargs="*")
    args = ap.parse_args(argv)
    urls = args.urls or UNSEEN_POLICY_URLS
    if not urls:
        print("No URLs. TODO(team): add unseen policy links to UNSEEN_POLICY_URLS or pass them as arguments.")
        save_result("live_mode_check", run_meta(status="pending: no unseen policy URLs given yet", rows=[]))
        return 0
    rows = [check(u) for u in urls]
    save_result("live_mode_check", run_meta(rows=rows, error_codes=sorted(CODES)))
    with (RESULTS / "live_mode_check.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["url", "hospital", "field", "reader_value", "page", "confidence", "quote_found", "needs_checking",
                    "reader_quote", "hand_check_value", "reader_right", "checked_by"])
        for r in rows:
            if "error" in r:
                w.writerow([r["url"], "", "ERROR", f"{r.get('code', '')}: {r['error']}", "", "", "", "", "", "", "", ""])
                continue
            for name, f in r["fields"].items():
                w.writerow([r["url"], r["hospital"], name, f["value"], f["page"], f["confidence"], f["verified"],
                            f["needs_checking"], f["source_quote"], "", "", ""])
    for r in rows:
        print(r["url"], "->", r.get("hospital") or r.get("error"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
