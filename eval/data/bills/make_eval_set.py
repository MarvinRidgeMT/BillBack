"""Build the bill eval set: one <name>.truth.json per bill, plus two blurred copies made with Pillow.

Ground truth comes from sample_bills/answer_key.csv, the values C typed into the bill generator
(sample_bills/make_sample_bills.py), never from model output. The bill images stay in sample_bills/;
each truth file points at its image with `file` (repo-relative) so nothing is stored twice.

Condition tag (one of clean | angled | crumpled | dim | blurry) = the hardest condition on the bill, in the order
blurry > dim > crumpled > angled > clean. Text PDFs are tagged clean. All conditions are kept in `conditions`.

    .venv/bin/python eval/data/bills/make_eval_set.py
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from PIL import Image, ImageFilter

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
KEY = REPO / "sample_bills" / "answer_key.csv"
SEVERITY = ("blurry", "dim", "crumpled", "angled", "clean")
_WORDS = {"blur": "blurry", "dim": "dim", "crumpled": "crumpled", "angled": "angled", "clean": "clean", "pdf": "clean"}
# Blurred copies for the "blurry" condition and the image-quality check. (source bill, Gaussian radius in px)
BLURRED = {"bill_11_blurry": ("bill_01_clean.jpg", 3.0), "bill_12_very_blurry": ("bill_05_crumpled.jpg", 7.0)}


def conditions_of(label: str) -> list[str]:
    found = {tag for word, tag in _WORDS.items() if word in label.lower()}
    return [c for c in SEVERITY if c in found] or ["clean"]


def truth_record(row: dict, file: str, conditions: list[str], note: str) -> dict:
    return {
        "file": file,
        "condition": conditions[0],
        "conditions": conditions,
        "hospital_name": row["hospital_name"],
        "hospital_address": row["hospital_address"],
        "amount_due": row["amount_due"],
        "service_date": row["service_date"],
        "account_number": row["account_number"],
        "hospital_slug": row["hospital_slug"],
        "state": row["state"],
        "source": note,
    }


def main() -> int:
    rows = {r["file"]: r for r in csv.DictReader(KEY.open())}
    for name, row in rows.items():
        conds = conditions_of(row["condition"])
        record = truth_record(row, f"sample_bills/{name}", conds, "sample_bills/answer_key.csv (values typed into the bill generator)")
        (HERE / f"{Path(name).stem}.truth.json").write_text(json.dumps(record, indent=2) + "\n")
    for stem, (src, radius) in BLURRED.items():
        img = Image.open(REPO / "sample_bills" / src).convert("RGB").filter(ImageFilter.GaussianBlur(radius))
        img.save(HERE / f"{stem}.jpg", quality=85)
        conds = ["blurry"] + [c for c in conditions_of(rows[src]["condition"]) if c != "clean"]
        record = truth_record(rows[src], f"eval/data/bills/{stem}.jpg", conds,
                              f"copy of {src} blurred with Pillow GaussianBlur(radius={radius}); truth = that bill's row")
        (HERE / f"{stem}.truth.json").write_text(json.dumps(record, indent=2) + "\n")
    print(f"wrote {len(rows) + len(BLURRED)} truth files to {HERE.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
