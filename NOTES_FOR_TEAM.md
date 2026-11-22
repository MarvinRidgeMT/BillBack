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

## Policy reader status (A)
- Tests: `.venv/bin/pytest -q` (no live API calls; the live test skips without `GEMINI_API_KEY`).
- Run one: `.venv/bin/python -m backend.policy_reader.cli data/policies/foo.pdf`
- Run all: `.venv/bin/python -m backend.policy_reader.cli --all data/policies/`
- API: `POST /api/policy/read` (multipart `file`, or JSON `{"url": ...}`); run with `.venv/bin/uvicorn backend.app:app`.
- OCR: tesseract isn't installed on Anish's laptop (Homebrew permissions problem). Scanned pages fall back to sending the raw PDF to Gemini, flagged with a "sent as raw PDF" warning. Quotes from those pages can't be verified, so they always go to review.

## Spot-checks (filled after the live run)
_TBD_
