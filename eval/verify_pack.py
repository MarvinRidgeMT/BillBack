"""Build the human verification pack for B's 20 real policies (17 reachable).

    python -m eval.verify_pack     -> eval/verify/answer_key.csv  (+ eval/verify/rows.js for index.html)

One row per (policy, field) with the reader's value, its quote + page, and the page text around keywords
(pulled with pdfplumber) so a person can check each field quickly. `correct_value`, `is_correct` and `verified_by`
are left BLANK: only a person reading the PDF fills them. No AI calls.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

import pdfplumber

from backend.policy_reader.cache import REPO_ROOT
from eval.answer_key_real import _fields, _load

OUT_DIR = REPO_ROOT / "eval" / "verify"
CSV_PATH = OUT_DIR / "answer_key.csv"
COLUMNS = ["policy_id", "hospital", "field", "reader_value", "reader_quote", "page", "evidence", "pdf_path", "pdf_url",
           "correct_value", "is_correct", "verified_by"]
# B's 20 real policies. None has a person-verified key yet. slug None = policy PDF not reachable.
POLICIES = [
    ("HOSP-R001", "Adventist Health", None),
    ("HOSP-R003", "baptist-health-south-florida", "baptist-health-south-florida"),
    ("HOSP-R007", "texas-health", "texas-health-resources-texas-health"),
    ("HOSP-R009", "uw-medicine", "uw-medicine-harborview-medical-center-uw-medical-center-airl"),
    ("HOSP-R010", "uchealth", "uchealth"),
    ("HOSP-R012", "emory", "emory-healthcare"),
    ("HOSP-R013", "banner", "banner-health"),
    ("HOSP-R002", "los-angeles-county-department-of-health-services", "los-angeles-county-department-of-health-services"),
    ("HOSP-R004", "baycare-health-system", "baycare-health-system"),
    ("HOSP-R005", "heartland-health-services", "heartland-health-services"),
    ("HOSP-R006", "deaconess", "deaconess-regional-healthcare-services-illinois-inc-heartlan"),
    ("HOSP-R008", "washington-hospital", "washington-hospital-healthcare-system"),
    ("HOSP-R011", "childrens-colorado", "children-s-hospital-colorado"),
    ("HOSP-R014", "novant", "novant-health-north-carolina-hospitals-provider-based-clinic"),
    ("HOSP-R015", "Mission Health", None),
    ("HOSP-R016", "duke", "duke-university-health-system"),
    ("HOSP-R017", "fort-healthcare", "fort-healthcare-inc"),
    ("HOSP-R018", "mercy", "mercy-mercy-revenue-cycle"),
    ("HOSP-R019", "ochsner", "ochsner-health"),
    ("HOSP-R020", "Ascension", None),
]
KEYWORDS = {
    "free_care %": ["free", "100%", "poverty", "FPL", "full"],
    "discount max %": ["discount", "poverty", "FPL", "%"],
    "discount tiers": ["discount", "%", "FPL", "sliding"],
    "asset test": ["asset", "resources", "savings"],
    "residency": ["resident", "reside", "service area", "county", "live"],
    "application window": ["days", "apply", "application", "240", "deadline"],
}
WINDOW = 160  # characters of context on each side of a keyword
MAX_SNIPPETS = 4


def _pdf_for(slug: str, url: str) -> Path | None:
    direct = REPO_ROOT / "data" / "policies" / f"{slug}.pdf"
    if direct.exists():
        return direct
    with (REPO_ROOT / "data" / "policies" / "sources.csv").open(newline="") as fh:
        for row in csv.DictReader(fh):
            if url and row.get("url") == url:
                p = REPO_ROOT / "data" / "policies" / row["file"]
                return p if p.exists() else None
    return None


def _snippets(text: str, words: list[str]) -> list[str]:
    spans: list[tuple[int, int]] = []
    for w in words:
        for m in re.finditer(re.escape(w), text, flags=re.IGNORECASE):
            s, e = max(0, m.start() - WINDOW), min(len(text), m.end() + WINDOW)
            if spans and s <= spans[-1][1]:
                continue
            spans.append((s, e))
            if len(spans) >= MAX_SNIPPETS:
                break
        if len(spans) >= MAX_SNIPPETS:
            break
    return ["…" + " ".join(text[s:e].split()) + "…" for s, e in sorted(spans)]


def _evidence(pages: list[str], page: str, field: str) -> str:
    """Page text around this field's keywords: the reader's cited page first, else the first pages that hit."""
    words = KEYWORDS[field]
    order = []
    if page and str(page).isdigit() and 1 <= int(page) <= len(pages):
        order.append(int(page))
    order += [i for i in range(1, len(pages) + 1) if i not in order]
    out: list[str] = []
    for p in order:
        snips = _snippets(pages[p - 1], words)
        if snips:
            out.append(f"[p{p}] " + " / ".join(snips))
        if len(out) >= 2:
            break
    return "\n".join(out) or "(no keyword found in the PDF text; the PDF may be scanned)"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows, unreachable = [], []
    for pid, name, slug in sorted(POLICIES):
        if slug is None:
            unreachable.append((pid, name))
            continue
        rules = _load(slug)
        url = rules.source.url if rules.source else ""
        pdf = _pdf_for(slug, url or "")
        pages: list[str] = []
        if pdf:
            with pdfplumber.open(pdf) as doc:
                pages = [pg.extract_text() or "" for pg in doc.pages]
        for label, value, ev in _fields(rules):
            page = ev.page or ""
            rows.append({
                "policy_id": pid, "hospital": rules.hospital_name, "field": label, "reader_value": value,
                "reader_quote": ev.quote or "", "page": page,
                "evidence": _evidence(pages, str(page), label) if pages else "(PDF not saved in the repo; open pdf_url)",
                "pdf_path": pdf.relative_to(REPO_ROOT).as_posix() if pdf else "", "pdf_url": url or "",
                "correct_value": "", "is_correct": "", "verified_by": "",
            })
    with CSV_PATH.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    (OUT_DIR / "rows.js").write_text("window.VERIFY_ROWS = " + json.dumps(rows, indent=1) + ";\n"
                                     "window.VERIFY_COLUMNS = " + json.dumps(COLUMNS) + ";\n")
    n_pol = len({r["policy_id"] for r in rows})
    print(f"wrote {CSV_PATH.relative_to(REPO_ROOT)}: {len(rows)} rows, {n_pol} policies; "
          f"not reachable (left out): {', '.join(f'{p} {n}' for p, n in unreachable)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
