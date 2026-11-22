"""Thin slice: bill -> cached policy -> eligibility (STUB engine).

python -m backend.e2e_cli <bill> --policy usa-health --household 3 --income 40000 --state AL [--fpl-table PATH]
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import sys
from pathlib import Path

from backend import eligibility_stub, fpl
from backend.bill_reader.reader import read_bill


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("bill", type=Path)
    p.add_argument("--policy", required=True, help="cached policy slug, e.g. usa-health")
    p.add_argument("--household", type=int, required=True)
    p.add_argument("--income", type=float, required=True)
    p.add_argument("--state", required=True)
    p.add_argument("--fpl-table", type=Path, help="override data/fpl_2026.json (e.g. the FAKE test fixture)")
    a = p.parse_args(argv)

    bill = read_bill(a.bill.read_bytes(), mimetypes.guess_type(a.bill.name)[0] or "")
    rules, policy_path = eligibility_stub.load_policy(a.policy)
    table = fpl.load_table(a.fpl_table) if a.fpl_table else None
    pct = fpl.percent_of_fpl(a.income, a.household, a.state, table=table)
    decision = eligibility_stub.decide(pct, rules)
    out = {
        "bill": {k: v.value for k, v in bill.fields.items()},
        "bill_fields_to_confirm": bill.fields_to_confirm,
        "policy": {"hospital": rules.hospital_name, "file": policy_path.name, "source_url": eligibility_stub.source_url(rules)},
        "fpl_table": "FAKE TEST FIXTURE" if a.fpl_table else "data/fpl_2026.json",
        "percent_of_fpl": round(pct, 2),
        "result": decision,
    }
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
