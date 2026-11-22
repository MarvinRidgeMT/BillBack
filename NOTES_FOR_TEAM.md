# Notes for the team

## For B — rules JSON contract (policy reader → rules engine)
- Pydantic models: `backend/policy_reader/schema.py` (`PolicyRules`). Example: `backend/tests/fixtures/sample_rules.json`.
  Load with `PolicyRules.model_validate_json(path.read_text())`, or just `json.load` it.
- Outputs land in `cache/policies/<hospital-slug>__<sha8>.json`.
- Added beyond the original draft (additive, safe to ignore):
  - `schema_version` ("1.0")
  - `evidence.verified`: `true` = quote found in the PDF text, `false` = not found (confidence capped at 0.5), `null` = field not stated
  - `review_fields`: which of the 6 fields are < 0.8 confidence or unverified
- **Question:** when a policy never mentions assets/residency, I return `applies`/`required` = `null` (not `false`), with confidence ≤ 0.3, so `needs_human_review` is true.
  Does your answer key label "not mentioned" as `false` or `null`? Tell me and I'll match it. Suggested engine rule: `null` = no restriction, but show "policy doesn't say" to the patient.
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
- Every policy has `needs_human_review: true`. Mostly that's by design: residency or asset test isn't stated, so confidence is ≤ 0.3. See the question for B above.
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
