"""End-to-end households: 10 households x their sample bill through the real pipeline, plus B's hand-worked key.

Part 1 (eval/data/households.json): bill read -> hospital match -> cached real policy -> POST /api/eligibility ->
POST /api/packet, compared with the expected status worked out by hand (arithmetic in the JSON).
Bill reads come from cache/bills (the saved reads of the sample bills, no model call) unless --live.

Part 2: B's hand-calculated answer key (data/answer_key.json: 10 households x 20 synthetic policies) through B's engine
with the 2026 table, via eval/households.py (unchanged).

    .venv/bin/python -m eval.run_households [--live]
Writes eval/results/households_e2e.json.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from typing import Any, Optional

from fastapi.testclient import TestClient

from backend import app as app_module
from backend import demo_mode
from eval.common import DATA, REPO, content_type, load_bill_truths, load_result, run_meta, save_result


def _bill_read(client: TestClient, truth: dict[str, Any], live: bool) -> tuple[dict[str, Any], str]:
    data = truth["path"].read_bytes()
    if not live:
        hit = demo_mode.cached_bill(hashlib.sha256(data).hexdigest())
        if hit is not None:
            return hit, "cache/bills"
    resp = client.post("/api/bill/read", files={"file": (truth["path"].name, data, content_type(truth["path"]))})
    resp.raise_for_status()
    return resp.json()["data"], "live"


def run_one(client: TestClient, hh: dict[str, Any], truth: dict[str, Any], live: bool) -> dict[str, Any]:
    t0 = time.perf_counter()
    bill, source = _bill_read(client, truth, live)
    f = bill["fields"]
    match = client.post("/api/hospitals/match", json={"hospital_name": f["hospital_name"]["value"],
                                                      "hospital_address": f["hospital_address"]["value"]}).json()["data"]
    slug = match["slug"]
    body = {"hospital_slug": slug, "household_size": hh["household_size"], "annual_income": hh["annual_income"],
            "state": hh["state"]}
    if hh.get("assets_usd") is not None:
        body["assets_usd"] = hh["assets_usd"]
    elig_resp = client.post("/api/eligibility", json=body)
    elig = elig_resp.json().get("data") or {}
    packet_ok = False
    if elig_resp.status_code == 200:
        ev = elig.get("evidence") or {}
        packet = client.post("/api/packet", json={
            "bill": {k: (v.get("value") or "") for k, v in f.items()}, "hospital_slug": slug,
            "household_size": hh["household_size"], "annual_income": hh["annual_income"],
            "eligibility": {"status": elig["status"], "percent_of_fpl": elig["percent_of_fpl"], "quote": ev.get("quote") or "",
                            "page": ev.get("page"), "fpl_year": elig.get("fpl_year")},
            "lang": "en"})
        packet_ok = packet.status_code == 200 and packet.content.startswith(b"%PDF")
    tier = elig.get("tier") or {}
    got_discount = tier.get("value") if tier.get("discount_type") == "percent_off" else None
    status_ok = elig.get("status") == hh["expected_status"]
    discount_ok = hh.get("expected_discount_percent") is None or got_discount == hh["expected_discount_percent"]
    return {
        "id": hh["id"], "bill": hh["bill"], "bill_source": source,
        "matched_slug": slug, "slug_ok": slug == hh["hospital_slug"],
        "expected_status": hh["expected_status"], "status": elig.get("status"),
        "expected_discount_percent": hh.get("expected_discount_percent"), "discount_percent": got_discount,
        "percent_of_fpl": elig.get("percent_of_fpl"), "fpl_used": elig.get("fpl_used"), "fpl_region": elig.get("fpl_region"),
        "explanation": elig.get("explanation"), "packet_ok": packet_ok,
        "correct": bool(slug == hh["hospital_slug"] and status_ok and discount_ok and packet_ok),
        "seconds": time.perf_counter() - t0,
    }


def b_key_summary() -> Optional[dict[str, Any]]:
    """Re-run B's hand-worked key (eval/households.py) and return its saved numbers."""
    from eval import households

    households.main()
    return json.loads((REPO / "eval" / "results" / "households.json").read_text())


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--live", action="store_true", help="read each bill with the model instead of the saved read")
    args = ap.parse_args(argv)
    spec = json.loads((DATA / "households.json").read_text())
    truths = {t["name"]: t for t in load_bill_truths()}
    client = TestClient(app_module.app)
    rows = [run_one(client, hh, truths[hh["bill"]], args.live) for hh in spec["households"]]
    for r in rows:
        mark = "ok " if r["correct"] else "MISS"
        print(f"{mark} {r['id']} {r['matched_slug']:42} expected {r['expected_status']:22} got {r['status']} ({r['percent_of_fpl']}%)")
    b_key = b_key_summary()
    payload = run_meta(
        correct=sum(r["correct"] for r in rows), total=len(rows), rows=rows,
        expectations_by=spec["worked_by"], checked_by=spec["checked_by"],
        b_hand_key={k: b_key[k] for k in ("households_status_ok_2026", "households", "status_ok_2026", "n")} if b_key else None,
    )
    save_result("households_e2e", payload)
    print(f"E2E households: {payload['correct']}/{payload['total']} correct")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
