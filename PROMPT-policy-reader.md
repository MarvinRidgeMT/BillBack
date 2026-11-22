# Claude Code task: build the AI policy reader (Gate 2, due 2:00am ET)

Read `CLAUDE.md` first. You are helping Anish (Person A). It's ~midnight ET; Gate 2 is at **2:00am**. Budget: ~1h45m of build, 15 min of verification. Be fast and practical.

## Step 0 — orient (5 min max)
1. Check whether this folder already has the team repo (`git status`, look for `backend/`, `frontend/`). If not, ask me for the GitHub URL and clone it here. If there is no repo yet, `git init` and create the layout below.
2. Find what already exists from Gate 1: bill reader, `fpl_2026.json`, B's rules engine, any policy PDFs. Reuse them; don't rebuild.
3. Use `superpowers:writing-plans` to write a ≤10-line plan in `PLAN-policy-reader.md`, then start immediately. Don't wait for approval unless something in the repo contradicts this prompt.

## Goal
`policy_reader` takes a hospital financial assistance policy (PDF file, PDF bytes, or URL) and returns **rules JSON** matching the schema below, with a verbatim quote + page number + confidence for every field. Gate 2 = it works on **5 real policies** from B, outputs are saved, and B's rules engine can consume them.

## Layout (adapt to the existing repo if it differs)
```
backend/
  app.py                    # FastAPI app (may already exist)
  policy_reader/
    __init__.py
    schema.py               # pydantic models = the contract with B
    extract_text.py         # pdfplumber per page; OCR fallback for scanned pages
    reader.py               # Gemini call + post-validation
    cache.py                # sha256(pdf bytes) -> cache/policies/<sha>.json
    cli.py                  # python -m backend.policy_reader.cli <pdf|url> [--out path]
  prompts/
    policy_reader.md        # the Gemini prompt (draft below)
  tests/
    test_policy_reader.py
data/policies/              # B's PDFs (+ sources.csv with url, download date)
cache/policies/             # rules JSON outputs (commit these — they're the demo fallback)
.env.example                # GEMINI_API_KEY=, GEMINI_MODEL=
```

## The rules JSON schema (contract with B — confirm with B before changing)
Write this as pydantic v2 models in `schema.py`, and export a JSON Schema for Gemini structured output.

```jsonc
{
  "hospital_name": "string",
  "hospital_state": "two-letter code or null",
  "source": { "url": "string|null", "sha256": "string", "retrieved_at": "ISO date", "page_count": 0 },
  "policy_effective_date": "string|null",

  // ---- the 6 answer-key fields ----
  "free_care": {                         // 1. free-care limit
    "fpl_max_percent": 200,              //    number|null (income at/below this % FPL = free)
    "evidence": { "quote": "verbatim text", "page": 3, "confidence": 0.95 }
  },
  "discount": {                          // 2. discount limit + 3. discount amount
    "fpl_max_percent": 400,              //    number|null (upper bound for any discount)
    "tiers": [                           //    ordered, non-overlapping
      { "fpl_min_percent": 200.01, "fpl_max_percent": 300,
        "discount_type": "percent_off | pays_percent_of_charges | amount_generally_billed | sliding_scale | other",
        "value": 75, "description": "string" }
    ],
    "evidence": { "quote": "...", "page": 4, "confidence": 0.9 }
  },
  "asset_test": {                        // 4. asset test
    "applies": true,                     //    bool|null
    "details": "string|null",            //    e.g. "liquid assets over $10,000 count as income"
    "evidence": { "quote": "...", "page": 5, "confidence": 0.8 }
  },
  "residency": {                         // 5. residency rule
    "required": true,                    //    bool|null
    "area": "string|null",               //    e.g. "service area counties: X, Y" / "state of Ohio"
    "evidence": { "quote": "...", "page": 2, "confidence": 0.85 }
  },
  "application_window": {                // 6. how long patients have to apply
    "days": 240,                         //    int|null
    "counted_from": "first_post_discharge_billing_statement | date_of_service | discharge | other | null",
    "evidence": { "quote": "...", "page": 6, "confidence": 0.9 }
  },

  // ---- helpful extras (optional, don't block on these) ----
  "income_basis": "fpl_percent | income_table | both | unclear",
  "uses_income_table": false,            // true if thresholds are a dollar table, not % FPL
  "insured_patients_eligible": "bool|null",
  "presumptive_eligibility": "string|null",
  "how_to_apply": "string|null",          // address/phone/portal if stated
  "needs_human_review": false,           // true if any field < 0.8 or quote not verified
  "warnings": ["string"]
}
```
Notes:
- If a policy gives a **dollar income table** instead of % FPL, set `uses_income_table: true`, convert to % FPL only if the table clearly says it's based on a % of FPL; otherwise leave the percent null, put the table in `description`/`warnings`, and set `needs_human_review: true`.
- `null` means "the policy doesn't say" — never guess a number.

## Pipeline (build in this order)
1. **Text extraction** (`extract_text.py`): pdfplumber, page by page, keep page numbers. Also extract tables (`page.extract_tables()`) — FPL tiers are often in tables; render them as pipe-delimited text under the page.
   - A page with < 50 characters of text = scanned → OCR it (pdf2image at 300 dpi + pytesseract). Check `which tesseract` first; if it's missing, `brew install tesseract poppler`.
   - Fallback if OCR is unavailable or garbage: send the raw PDF bytes to Gemini as a PDF part (Gemini reads PDFs natively). Flag `warnings: ["sent as raw PDF"]`.
2. **Gemini call** (`reader.py`): `google-genai` SDK, model from `GEMINI_MODEL`, temperature 0, JSON output constrained to the pydantic schema. Input = the prompt from `prompts/policy_reader.md` + the page-tagged text (`=== PAGE 3 ===` markers). One call per policy; most FAPs are 5–25 pages, which fits easily.
   - Before writing the call, check the current docs for the installed SDK version (structured output config has changed between versions). Do a one-line smoke test first.
   - Retry once on a 429/5xx with a short backoff. Time each call.
3. **Post-validation — this is what makes the accuracy number trustworthy:**
   - Parse with pydantic; on a validation error, retry once with the error message appended.
   - **Quote verification:** normalize whitespace/case/quotes and check each `evidence.quote` actually appears in the extracted text of that page (fuzzy match, e.g. `rapidfuzz` partial_ratio ≥ 90). If not → cap that field's confidence at 0.5 and add a warning.
   - Sanity rules: `free_care.fpl_max_percent` ≤ `discount.fpl_max_percent`; tiers ordered and non-overlapping; percents in 100–1000; window days in 30–730. Violations → warning + lower confidence.
   - `needs_human_review = any(confidence < 0.8) or any quote unverified`.
4. **Cache** (`cache.py`): key = sha256 of the PDF bytes. Hit → return instantly. Save to `cache/policies/<hospital-slug>__<sha8>.json`. Commit these files.
5. **CLI** (`cli.py`): `python -m backend.policy_reader.cli data/policies/foo.pdf` prints the JSON and timing; `--all data/policies/` runs every PDF and prints a summary table (hospital, free %, discount %, asset test, residency, window, needs_review, seconds).
6. **API**: `POST /api/policy/read` accepting either a file upload or `{ "url": "..." }`. URL fetch: httpx, follow redirects, 20 s timeout, 25 MB cap, must return `application/pdf` (or an HTML page — then find the first `.pdf` link containing "financial", "assistance", "charity" or "FAP"). This endpoint is what live mode uses at 7am, so keep it simple now.
7. **Bridge to B**: confirm B's rules engine can load one of the cached JSONs. If B's engine expects a different shape, write a small adapter function rather than changing both sides at 1:30am.

## Tests (use `superpowers:test-driven-development`; keep them fast — no live API calls in pytest)
- schema round-trip with a fixture JSON
- quote verification: exact match passes, invented quote fails, whitespace/hyphenation differences pass
- sanity checks flag free% > discount% and overlapping tiers
- scanned-page detection triggers OCR path (mock pytesseract)
- cache hit returns without calling Gemini (mock the client)
- an optional `@pytest.mark.live` test that runs one real policy, skipped unless `GEMINI_API_KEY` is set

## Gate 2 checklist (use `superpowers:verification-before-completion` — show real output, don't just claim it)
- [ ] `pytest` green (mine + B's)
- [ ] `cli --all` run on **5 real policies**, including at least one with an income table or asset test, and the scanned one if B has it
- [ ] 5 JSONs in `cache/policies/`, each with quotes that verify
- [ ] Spot-check 2 of them by hand against the PDF — write what you found in `NOTES_FOR_TEAM.md` (this seeds the README "Limits" section)
- [ ] Note average seconds and estimated cost per policy
- [ ] `.env` gitignored, `.env.example` present, no keys in `git log -p`
- [ ] Committed and pushed. Tell me the commit hash.

## Don't
- Don't let the model compute eligibility or FPL math. Thresholds only.
- Don't build the live-mode UI, auth, or anything in "nice to have." That's after 7am or never.
- Don't spend more than 15 minutes stuck on OCR — fall back to raw-PDF-to-Gemini and move on.

---

## Draft Gemini prompt → save as `backend/prompts/policy_reader.md` (tune with `prompt-design:prompt-design`)

```
You are extracting rules from a U.S. nonprofit hospital's Financial Assistance Policy (FAP), also called a charity care policy. Your output is read by software that decides whether a low-income patient likely qualifies, so accuracy matters more than completeness.

The policy text is below, split into pages marked "=== PAGE n ===". Tables appear as pipe-delimited rows.

Extract these fields into the provided JSON schema:
1. free_care.fpl_max_percent — the highest household income, as a percent of the Federal Poverty Level (FPL/FPG), at which care is 100% free.
2. discount.fpl_max_percent — the highest income (% FPL) that gets any discount.
3. discount.tiers — each discount band: its FPL range and what the patient gets (e.g. "75% off", "pays the Amount Generally Billed", "sliding scale"). Keep the policy's own boundaries exactly ("up to and including 200%" -> max 200).
4. asset_test — whether assets (savings, property, investments) are considered, and how.
5. residency — whether patients must live in a specific state, county, or service area, and which.
6. application_window — how many days a patient has to apply, and what the clock starts from.

Rules:
- Every field needs evidence: copy the exact sentence(s) from the policy (verbatim, no paraphrase, under 60 words) and the page number it appears on. Do not invent or merge quotes.
- If the policy does not state something, use null and confidence 0.0-0.3. Never guess or use typical values (e.g. do not assume 200%/400% or 240 days).
- If thresholds are a dollar income table rather than % of FPL, set uses_income_table=true. Only fill fpl_max_percent if the policy explicitly states the % of FPL the table is based on.
- "Federal Poverty Guidelines", "FPG", "FPL" and "poverty level" all mean the same thing.
- If several hospitals or facilities are covered, extract the rules that apply to the hospital named in the title, and add a warning.
- If the policy contradicts itself, use the more specific statement (e.g. the table over the summary) and add a warning.
- Confidence: 0.9-1.0 = stated explicitly in one place; 0.6-0.89 = needed light interpretation; below 0.6 = unclear or inferred.
- Do not decide anyone's eligibility. Do not add advice.
```
