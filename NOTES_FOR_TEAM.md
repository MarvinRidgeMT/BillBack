# Notes for the team

## For B — rules JSON contract (policy reader → rules engine)
- Pydantic models: `backend/policy_reader/schema.py` (`PolicyRules`). Example: `backend/tests/fixtures/sample_rules.json`.
  Load with `PolicyRules.model_validate_json(path.read_text())`, or just `json.load` it.
- Outputs land in `cache/policies/<hospital-slug>__<sha8>.json`.
- Added beyond the original draft (additive, safe to ignore):
  - `schema_version` ("1.0")
  - `evidence.verified`: `true` = quote found in the PDF text, `false` = not found (confidence capped at 0.5), `null` = field not stated
  - `review_fields`: which of the 6 fields need review (`unclear`, < 0.8 confidence, or a stated quote that didn't verify)
  - **NEW `evidence.status`**: `"stated"` | `"not_stated"` | `"unclear"`. Additive; old JSONs default to `"stated"`.
    - `not_stated` = the policy doesn't address it. Value stays `null`, quote is empty, confidence ≥ 0.85. **Engine/UI rule: no restriction, but tell the patient "the policy doesn't say".**
    - `unclear` = ambiguous or contradictory. Always in `review_fields`.
- **Question (still open):** does your answer key label "not mentioned" as `null` or `false`? It's one setting: `NOT_STATED_ANSWER_KEY_VALUE` in `backend/eval_config.py` (currently `None`). Compare predictions through `eval_config.comparable_value(value, status)`.
- Tier boundaries are copied as written ("201%–300%" → min 201, max 300). So treat incomes between 200 and 201 % FPL as belonging to the lower band.

## For everyone — model provider changed (A, 1:00am)
- The policy reader now uses **Claude Sonnet 5.5** (`claude-sonnet-5-5`, Anthropic API) instead of Gemini, because we had Anthropic credits and no Gemini key. Gemini is still supported: set `LLM_PROVIDER=gemini`.
- `.env` needs `ANTHROPIC_API_KEY` (see `.env.example`). Ask Anish for the key; don't paste it in chat or git.
- Text pages only go out as extracted text. A PDF with scanned pages is sent whole as a PDF document block.

## Policy reader status (A)
- Tests: `.venv/bin/pytest -q` (no live API calls; the live test skips when no API key is set).
- Run one: `.venv/bin/python -m backend.policy_reader.cli data/policies/foo.pdf`
- Run all: `.venv/bin/python -m backend.policy_reader.cli --all data/policies/`
- API: `POST /api/policy/read` (multipart `file`, or JSON `{"url": ...}`); run with `.venv/bin/uvicorn backend.app:app`.
- OCR: tesseract isn't installed on Anish's laptop (Homebrew permissions problem). Scanned pages fall back to sending the raw PDF to the model, flagged with a "sent as raw PDF" warning. Quotes from those pages can't be verified, so they always go to review.

## Gate 2 live run — 6 real policies (2026-11-22 ~1:00am, Claude Sonnet 5.5, effort medium)
- All 6 parsed and validated. **Avg 8.4 s and ~$0.042 per policy** (≈15.0k input / 1.2k output tokens). Cached re-reads: instant, $0.
- ~~Every policy has `needs_human_review: true`~~ → fixed with `evidence.status` (re-run 1:00am, same cost):

  | | before | after |
  |---|---|---|
  | fields needing review | 11 / 30 | **4 / 30** |
  | policies needing review | 6 / 6 | **4 / 6** |

  Remaining 4 are real ambiguity: Adena asset test (only on the application form → `unclear`), Baptist free care written as "< 200%", Boys Town + USA Health application window wording.
- Raw model output is now saved in `cache/policies/raw/<sha8>.raw.json`. After changing validation code: `.venv/bin/python -m backend.policy_reader.cli --revalidate data/policies/` (no API call, $0).
- All 6 happen to be 200% free / 400% discount / 240 days. **We haven't tested a non-standard policy yet** (e.g. 300% free care or a dollar income table). B, please include at least one of those in the 20.
- `och-ms.pdf` is the **Baptist Memorial Health Care** system-wide policy, hosted on och.org, so the hospital name "Baptist Memorial" is correct for that file.

### Hand spot-checks against the PDF text
**USA Health (AL):** 5 of 6 fields clearly right, 1 ambiguous in the source.
- Free ≤ 200% ✓. Discount to 400% ✓. Tiers 200–300% = 85%, 300–400% = 75% ✓. The source table's boundaries overlap at 200 and 300; the model flagged that.
- Asset test ✓: "assets that exceed 25% of such patient's household income may not be eligible" (p5).
- Residency `null` ✓: covered facilities are in Mobile/Baldwin counties, but patients don't have to live there.
- **Window: the policy contradicts itself.** The definitions (p2) say 240 days after the first post-discharge bill; Procedure B (p4) says 240 days past the date of service. The model picked the date of service, flagged the conflict, and gave confidence 0.75, so it goes to review. → README "Limits" example.

**Boys Town (NE):** 6 of 6 match the PDF.
- Free ≤ 200% ✓. Discount to 400% ✓. Tiers 201–250% = 75%, 251–300% = 50%, 301–400% = 25% ✓. These came from the table; the prose only says "up to 75%", and the model noted that.
- Asset test ✓ (cash on hand / liquid assets count). Residency `null` ✓ (none stated; Nebraska is only mentioned for the AGB method).
- Window: 240 days from "1st billed date, post discharge date or date of service". The source is ambiguous; confidence 0.7, goes to review.

### Honest failures / limits found (for README "Limits")
1. **My bug, fixed:** quote verification rejected real short table-row quotes ("< 200% 100%"). Now quotes of 6–24 characters must match exactly, and only longer ones use fuzzy matching.
2. **Probably a wrong extraction:** Adena `asset_test.applies = true` rests only on an application-form checkbox ("income AND asset verification"), not on a policy rule. Confidence 0.6, so it's flagged, not used silently.
3. **Text extraction noise:** USA Health has a "COPY" watermark that pdfplumber mixes into the text ("COconsideration PYgranted"). Quotes still verified, but watermarked PDFs could break quote matching.
4. Claude structured outputs allow at most 16 nullable fields. Unstated text comes back as `""` and unstated page/days as `0`, and code converts those to `null`, so the JSON B sees is unchanged.

## New since Gate 2 (A, ~1:00am)

### For B
- **FPL math exists — please import it, don't duplicate:** `from backend.fpl import poverty_line, percent_of_fpl`. `percent_of_fpl(annual_income, household_size, state)` → e.g. `200.0` = exactly 200%, not rounded. AK and HI have their own rows; DC and the other states use the 48-state row. Raises `ValueError` for household < 1, negative income, or a bad state code.
- ⚠️ **`data/fpl_2026.json` is NOT in the repo yet.** The HHS ASPE page (https://aspe.hhs.gov/topics/poverty-economic-mobility/poverty-guidelines) returned 502 on every try, and we won't type numbers from memory. Tests use a FAKE table (`backend/tests/fixtures/fpl_test_table.json`). Format for the real file: `{"year": 2026, "source_url": ..., "retrieved_at": ..., "tables": {"contiguous"|"AK"|"HI": {"base": {"1".."8": dollars}, "additional_person": dollars}}}`.
- `backend/eligibility_stub.py` is a **STUB — replace it with your engine** and keep the output keys if you can: `status` (`likely_free` / `likely_discounted` / `probably_not_eligible` / `cannot_determine`), `tier`, `evidence` (quote, page, confidence, verified), `caveats`, `disclaimer`.
- `POST /api/eligibility` `{hospital_slug, household_size, annual_income, state}` uses the stub. It returns 503 until `fpl_2026.json` exists.

### For C (UI)
- `POST /api/bill/read` — multipart field `file` (JPG / PNG / HEIC / PDF, ≤ 15 MB). The response uses the same envelope as the other endpoints: `{success, data: {fields, fields_to_confirm, seconds, model}, error}`.
  - Each field is `{value, confidence, note, normalized}`. `normalized` is cents (int) for `amount_due` and an ISO date for `service_date`.
  - Show every field listed in `fields_to_confirm` to the patient to confirm or edit.
  - **No patient name, DOB or insurance ID is ever returned** — by design.
- Live run on our 3 FAKE bills (`backend/tests/fixtures/bills/`, regenerate with `python -m backend.tests.fixtures.bills.make_bills`): **15/15 fields correct, 2.3–2.9 s, ≈ $0.006–0.011 per bill** (Sonnet 5.5 at $2/$10 per 1M tokens).
- End to end from the CLI: `python -m backend.e2e_cli <bill> --policy usa-health --household 3 --income 30000 --state AL [--fpl-table backend/tests/fixtures/fpl_test_table.json]`.

### OCR (Anish)
- `brew install tesseract poppler` fails because `/opt/homebrew` isn't writable by your user. Run this yourself (it asks for your Mac password), then re-run the brew install:
  ```
  sudo chown -R $(whoami) /opt/homebrew
  brew install tesseract poppler
  ```
  Until then, scanned PDFs go to the model as a PDF (works, but their quotes can't be verified).
