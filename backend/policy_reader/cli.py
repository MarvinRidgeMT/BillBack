"""python -m backend.policy_reader.cli <pdf|url> [--out path] [--no-cache]
python -m backend.policy_reader.cli --all data/policies/
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from .fetch import fetch_policy_pdf
from .reader import ReadResult, read_policy


def _load(target: str) -> tuple[bytes, Optional[str]]:
    if target.startswith(("http://", "https://")):
        return fetch_policy_pdf(target)
    return Path(target).read_bytes(), None


def _fmt(value) -> str:
    return "-" if value is None else str(value)


def _row(name: str, r: ReadResult) -> list[str]:
    rules = r.rules
    return [
        name[:28],
        rules.hospital_name[:30],
        _fmt(rules.free_care.fpl_max_percent),
        _fmt(rules.discount.fpl_max_percent),
        _fmt(rules.asset_test.applies),
        _fmt(rules.residency.required),
        _fmt(rules.application_window.days),
        "YES" if rules.needs_human_review else "no",
        ",".join(rules.review_fields) or "-",
        "cache" if r.cached else f"{r.seconds:.1f}",
    ]


HEADERS = ["file", "hospital", "free%", "disc%", "assets", "resid", "days", "review", "review_fields", "sec"]


def _print_table(rows: list[list[str]]) -> None:
    widths = [max(len(h), *(len(r[i]) for r in rows)) for i, h in enumerate(HEADERS)]
    line = lambda cells: "  ".join(c.ljust(w) for c, w in zip(cells, widths))  # noqa: E731
    print(line(HEADERS))
    print(line(["-" * w for w in widths]))
    for r in rows:
        print(line(r))


def run_all(folder: Path, use_cache: bool) -> int:
    pdfs = sorted(folder.glob("*.pdf"))
    if not pdfs:
        print(f"no PDFs in {folder}", file=sys.stderr)
        return 1
    rows, fresh, failures = [], [], []
    for pdf in pdfs:
        try:
            result = read_policy(pdf.read_bytes(), use_cache=use_cache)
        except Exception as exc:  # keep going; report every failure at the end
            failures.append((pdf.name, str(exc)))
            continue
        rows.append(_row(pdf.name, result))
        if not result.cached:
            fresh.append(result)
    if rows:
        _print_table(rows)
    if fresh:
        avg_s = sum(r.seconds for r in fresh) / len(fresh)
        avg_in = sum(r.input_tokens for r in fresh) / len(fresh)
        avg_out = sum(r.output_tokens for r in fresh) / len(fresh)
        costs = [c for c in (r.estimated_cost_usd() for r in fresh) if c is not None]
        cost = f"${sum(costs) / len(costs):.4f}" if costs else "n/a (set GEMINI_PRICE_*_PER_M)"
        print(f"\nfresh runs: {len(fresh)}  avg {avg_s:.1f}s  avg tokens in {avg_in:.0f} / out {avg_out:.0f}  avg cost {cost}")
    for name, err in failures:
        print(f"FAILED {name}: {err}", file=sys.stderr)
    return 1 if failures else 0


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Read a hospital financial assistance policy into rules JSON.")
    parser.add_argument("target", nargs="?", help="PDF path or URL")
    parser.add_argument("--all", type=Path, help="run every PDF in this folder and print a summary table")
    parser.add_argument("--out", type=Path, help="also write the rules JSON here")
    parser.add_argument("--no-cache", action="store_true", help="ignore cached results")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")

    if args.all:
        return run_all(args.all, use_cache=not args.no_cache)
    if not args.target:
        parser.error("give a PDF path/URL or --all <folder>")

    pdf_bytes, url = _load(args.target)
    result = read_policy(pdf_bytes, url=url, use_cache=not args.no_cache)
    text = result.rules.model_dump_json(indent=2)
    print(text)
    if args.out:
        args.out.write_text(text + "\n")
    where = "cache" if result.cached else f"{result.seconds:.1f}s, tokens in {result.input_tokens} / out {result.output_tokens}"
    print(f"\n[{where}] saved: {result.cache_path or 'already cached'}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
