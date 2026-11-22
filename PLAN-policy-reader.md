# Plan — policy reader (Gate 2, 2:00am ET)
1. Repo skeleton: `git init`, venv, `requirements.txt`, `.env.example` (GEMINI_API_KEY, GEMINI_MODEL=gemini-3.8-flash).
2. `schema.py`: pydantic v2 rules contract with B + `llm_json_schema()` (refs inlined, server-only fields stripped).
3. Tests first: schema round-trip, quote verification, sanity checks, OCR path (mocked), cache hit (mocked model).
4. `extract_text.py`: pdfplumber pages + tables as pipe rows; <50 chars → OCR, else flag for raw-PDF fallback.
5. `validate.py`: fuzzy quote check (rapidfuzz ≥ 90, page fix-up), sanity rules, `needs_human_review`.
6. `reader.py`: one Gemini call, temp 0, JSON schema output, 1 retry on 429/5xx, 1 retry on validation error, timing + tokens.
7. `cache.py` (sha256 → `cache/policies/<slug>__<sha8>.json`), `cli.py` (`--all` summary table), `POST /api/policy/read`.
8. Run live on 5 real FAPs, spot-check 2 by hand → `NOTES_FOR_TEAM.md`; commit and push.
