"""Thin slice: bill -> hospital match -> cached policy -> B's rules engine (2026 FPL).

python -m backend.e2e_cli <bill> [--policy SLUG] --household 3 --income 40000 --state AL [--assets 0]
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import sys
from pathlib import Path

from backend import fpl, policies
from backend.eligibility import eligibility_result_to_api_response, load_fpl_table_from_json, run_eligibility
from backend.bill_reader.reader import read_bill


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("bill", type=Path)
    p.add_argument("--policy", help="cached policy slug; default: match the bill's hospital")
    p.add_argument("--household", type=int, required=True)
    p.add_argument("--income", type=float, required=True)
    p.add_argument("--state", required=True)
    p.add_argument("--assets", type=float, help="household assets in dollars (needed when a policy has an asset test)")
    a = p.parse_args(argv)

    bill = read_bill(a.bill.read_bytes(), mimetypes.guess_type(a.bill.name)[0] or "")
    match = policies.match_hospital(bill.fields["hospital_name"].value, bill.fields["hospital_address"].value)
    slug = a.policy or match["slug"]
    if not slug or (not a.policy and not match["matched"]):
        print(json.dumps({"bill": {k: v.value for k, v in bill.fields.items()}, "match": match}, indent=2))
        return 1
    rules, policy_path = policies.load_policy(slug)
    table = fpl.load_table()
    pct = fpl.percent_of_fpl(a.income, a.household, a.state, table=table)
    result = run_eligibility(rules, a.household, a.income, a.state, load_fpl_table_from_json(table), fpl_year=int(table["year"]), assets_usd=a.assets)
    out = {
        "bill": {k: v.value for k, v in bill.fields.items()},
        "bill_fields_to_confirm": bill.fields_to_confirm,
        "match": match,
        "policy_file": policy_path.name,
        "result": eligibility_result_to_api_response(result, rules, pct, policies.source_url_for(rules)),
    }
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
