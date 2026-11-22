"""Rules JSON cache keyed by sha256 of the PDF bytes. Files are committed as the demo fallback."""

from __future__ import annotations

import hashlib
import logging
import re
from pathlib import Path
from typing import Optional

from pydantic import ValidationError

from .schema import PolicyRules

log = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CACHE_DIR = REPO_ROOT / "cache" / "policies"
_SHA_RE = re.compile(r"^[0-9a-f]{64}$")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug[:60] or "policy"


def lookup(sha: str, cache_dir: Path = DEFAULT_CACHE_DIR) -> Optional[PolicyRules]:
    if not _SHA_RE.match(sha):
        raise ValueError("sha must be a 64-char lowercase hex sha256")
    for path in Path(cache_dir).glob(f"*__{sha[:8]}.json"):
        try:
            rules = PolicyRules.model_validate_json(path.read_text())
        except (ValidationError, OSError) as exc:
            log.warning("ignoring unreadable cache file %s: %s", path, exc)
            continue
        if rules.source and rules.source.sha256 == sha:
            return rules
    return None


def save(rules: PolicyRules, cache_dir: Path = DEFAULT_CACHE_DIR) -> Path:
    if rules.source is None:
        raise ValueError("rules.source is required to cache")
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_dir / f"{slugify(rules.hospital_name)}__{rules.source.sha256[:8]}.json"
    path.write_text(rules.model_dump_json(indent=2) + "\n")
    return path
