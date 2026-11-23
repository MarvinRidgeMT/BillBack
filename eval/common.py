"""Shared helpers for the eval scripts: paths, run metadata, saving results, loading the bill set."""

from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "eval" / "data"
RESULTS = REPO / "eval" / "results"
BILLS_DIR = DATA / "bills"


def model_name() -> str:
    """The model the app is configured to use (what a live run will call)."""
    from dotenv import load_dotenv

    load_dotenv()  # same lookup as the app: .env here or in a parent folder
    provider = (os.getenv("LLM_PROVIDER") or "anthropic").lower()
    if provider == "gemini":
        return os.getenv("GEMINI_MODEL") or "gemini (GEMINI_MODEL unset)"
    return os.getenv("ANTHROPIC_MODEL") or "claude-sonnet-5-5"


def git_commit() -> str:
    """HEAD, plus '+uncommitted' when tracked code under backend/ or eval/ has changes not yet committed."""
    try:
        head = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=REPO, text=True).strip()
        dirty = subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=no", "--", "backend", "eval"],
                                        cwd=REPO, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"
    return f"{head}+uncommitted" if dirty else head


def run_meta(**extra: Any) -> dict[str, Any]:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "model": model_name(),
        "git_commit": git_commit(),
        **extra,
    }


def save_result(name: str, payload: dict[str, Any]) -> Path:
    RESULTS.mkdir(parents=True, exist_ok=True)
    path = RESULTS / f"{name}.json"
    path.write_text(json.dumps(payload, indent=2, default=str) + "\n")
    return path


def load_result(name: str) -> dict[str, Any] | None:
    path = RESULTS / f"{name}.json"
    return json.loads(path.read_text()) if path.exists() else None


def load_bill_truths() -> list[dict[str, Any]]:
    """Every eval/data/bills/*.truth.json, sorted by name, each with `name` and resolved `path`."""
    out = []
    for path in sorted(BILLS_DIR.glob("*.truth.json")):
        truth = json.loads(path.read_text())
        out.append({**truth, "name": path.name.removesuffix(".truth.json"), "path": REPO / truth["file"]})
    return out


def content_type(path: Path) -> str:
    return {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".pdf": "application/pdf"}.get(
        path.suffix.lower(), ""
    )
