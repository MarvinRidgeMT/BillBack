# Notes for the team

## FINAL NUMBERS FOR VIDEO (A, 11:10am — from `eval/results/SUMMARY.md`; say only these)
| Test | Measured | Target | Result |
|---|---|---|---|
| Bill extraction (10 fake bills × 5 fields) | 50/50 (100%) | ≥ 90% | ✅ met |
| Policy reader, hand spot-checks (2 real policies × 6 fields) | 11/12 (Boys Town 6/6, USA Health 5/6) | ≥ 90% | ✅ met (small sample, checked by hand) |
| Policy reader, 120-field answer key | not measured (no field-level key for real PDFs) | ≥ 90% | — not measured |
| Policy quotes verified verbatim in the PDF | 21/21 | all | ✅ met |
| Policy re-run agreement (6 policies × 5 values) | 29/30 | — | info |
| End-to-end households, status (10 households × 20 policies, 2026 FPL) | 10/10 households (200/200 results) | 10/10 | ✅ met |
| …same, every detail incl. unresolved-rule notes | 7/10 households (193/200) | — | info (B to confirm 7 notes) |
| Rules-engine + backend tests | 215 passed, 0 failed, 2 skipped | all pass | ✅ met |
| Speed, bill → result (cached policy) | avg 2.6 s, max 3.3 s | < 60 s | ✅ met |
| Speed, first bill for a new hospital (live policy read) | avg 10.9 s | < 60 s | ✅ met |
| Cost per bill (cached policy) | $0.0096 | < $0.05 | ✅ met |
| Cost, first bill for a new hospital | $0.0528 | < $0.05 | ❌ not met |
| Bill fields sent to the patient to confirm | 2/50 (under 0.8 confidence: 2) | — | info |
| Policy fields sent to human review | 4/30 | — | info |

Say it like this (all true, all measured):
- "On our 10 sample bills — crumpled, angled, dim — BillBack read **50 out of 50** fields correctly, in about **3 seconds** and about **one cent** per bill."
- "Every policy quote we show was found **word for word** in the hospital's PDF (21 of 21)."
- "The rules engine — plain code, no AI — gave the expected answer for **all 10** test households, using the **2026** federal poverty guidelines."
- Don't say "90% of 120 policy fields": we didn't measure that. Do say "we checked two policies by hand: 11 of 12 fields right".


## For B — 3 things before the video (A, 11:45am)
1. **B: fill `correct_value` for these 36 rows by 12:10; Anish reruns `eval/policy_reader.py`.**
   File: `eval/answer_key_real_TODO.csv` (6 real policies × 6 fields: Baptist Health FL, Texas Health TX, UW Medicine WA,
   UCHealth CO, Emory GA, Banner AZ). For each row open `pdf_url`, go to `page`, write the right value in `correct_value`
   and `yes`/`no` in `is_correct`. We did **not** fill any of it. Once every row has `is_correct`,
   `python -m eval.answer_key_real` prints the score and `python -m eval.summary` puts it in SUMMARY.md
   (until then SUMMARY says "pending").
2. **Your handoff's example `fpl_2026.json` has 2024 numbers.** The repo file `data/fpl_2026.json` is correct
   (2026 HHS: 15,960 + 5,680 per extra person; AK 19,950; HI 18,360). Nothing to change in the repo; just don't copy the example.
3. **Please confirm the 7 household detail notes** (193/200 detail match with 2026 numbers; status still 200/200).
   List: `eval/results/households.md`. Mostly an extra "unresolved residency rule" note.

Also new: `eval/results/b_scorer_on_reader_output.md` — your scorer on our 17 real reads converted to your
`HospitalPolicy` format (`data/person_a_output/`). **Completeness/format score, not accuracy:** avg 86.2/100, 0/17 pass,
because our schema has no `version` field (and 5 policies state no effective date). We left those null instead of guessing.

Cost note: a new hospital still costs **$0.0528** (target < $0.05, not met). We kept it rather than re-read policies
right before the freeze; trimming non-FAP pages is the planned fix.

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

## From C (front end) — for A, 2:30am
- **No CORS change needed.** The browser only talks to Next.js. `frontend/next.config.ts` rewrites `/api/:path*` → `${BACKEND_URL}/api/:path*` (default `http://localhost:8000`). For deploy, set `BACKEND_URL` on the front end host.
- **Ask: `GET /api/hospitals`** → `{success, data: [{slug, name, state}], error}` for every cached policy. Right now the 6 hospitals are hardcoded in `frontend/lib/hospitals.ts`, so the list goes stale when B adds policies.
- Things I saw in real `/api/eligibility` responses (the UI shows them as sent; I did not paper over them):
  1. **Discount quote doesn't match the tier.** USA Health at 214% FPL returns `tier.value = 85` (so the stamp says "85% OFF") but `evidence.quote` is "300-400% 75% FAP adjustment applied". The patient sees two different numbers. Could the evidence be the matched tier's line?
  2. **Caveats leak field names**, e.g. "Some policy details need confirming: application_window". Plain words would read better ("how long you have to apply").
  3. Baptist Memorial: the cached policy says `hospital_state: "TN"`, the design doc and `sources.csv` say MS. I send MS. Same FPL row either way, but which is right?
- The UI falls back to a clearly labeled **sample** (never shown as real) when `/api/eligibility` returns 503 or the backend is down, only if `NEXT_PUBLIC_DEMO_MODE=1`. It goes away by itself once `data/fpl_2026.json` exists.

## Integration done (A, 11:10am) — read this, B and C

### For B
- Your engine is live behind `POST /api/eligibility` via `backend/eligibility.py` (your bridge, with fixes):
  - FPL year now comes from `data/fpl_2026.json` (2026). It was 2024, and that's why the FPL evidence had `year: null` (regression test added).
  - The FPL region now comes from the **household's** state (AK/HI rows), not the hospital's.
  - A rule that's `unclear` or < 0.8 confidence becomes an unresolved condition, never a pass. A rule that's `not_stated` adds no condition.
  - Open-ended tiers (no upper %) are skipped. `needs_more_information` is sent to the UI as `cannot_determine`.
- `eval/households.py`: your 200 combinations reproduce **200/200 with 2024 numbers**. With 2026: **status 200/200**, but 7 results gain an extra unresolved-rule note (mostly residency; list in `eval/results/households.md`). **Please confirm that's expected.** The answer key was NOT edited.
- Your 20 "real" policy JSONs say `verification_status: unverified` / "PDF not opened". So I ran our policy reader on their URLs: **14/20 read**; 6 failed at the hospital sites (403/404/no PDF link). Results are in `eval/results/b_real_policies.md`. Duke's URL is the **application form**, not the policy, and Heartland is an FQHC sliding-fee schedule; both are flagged for review.
- I added an empty `scripts/__init__.py` so `eval/` can import your `dict_to_policy`. Nothing else in `scripts/` or `billback/` changed.

### For C
- **The API now matches your types:** 4 statuses, `tier` in the policy-tier shape, `evidence` (+ `source_url`), plain-word `caveats`, `disclaimer: "Likely eligible, not a guarantee."`. Extra keys: `explanation`, `missing_facts`, `fpl_year`, `engine_tier`.
- **`GET /api/hospitals` exists** (19 hospitals now) and `POST /api/hospitals/match {hospital_name, hospital_address}` → `{slug, score, matched}`. Your hardcoded 6 still work; switching the list over is optional — **don't change it before the video.**
- Your 3 observations: (1) the quote is now the field's quote; per-tier quotes need a schema change (after the hackathon). (2) caveats are plain words now. (3) Baptist: `TN` is the issuer (Memphis HQ); `MS` for OCH is fine — the FPL row is the same.
- **The UI doesn't ask about savings.** So USA Health and Boys Town (asset test stated) return `cannot_determine` with "We still need to know: how much you have in savings or property". The API takes an optional `assets_usd` if you ever add the question.
- The packet PDF isn't built ("Get my application" shows "coming in the next version"). Fine for the demo.
- **Video bill:** use `bill_10_crumpled_dim.jpg` (Fort HealthCare, WI). It's crumpled + dim, and its account number "FH 7735-0092" goes to the **confirm step** (it has a space, which our check rejects). With household 3 / $40,000 / WI it gives **Likely free care, 146% of FPL**, with the page 1 quote. `bill_09_text.pdf` (Marshfield) also gives a clean "likely free" result; I ran that one through the real UI.
- Demo with no API at all: `BILL_CACHE_ONLY=1 DEMO_CACHE_ONLY=1` on the backend. The 10 sample bills are served from `cache/bills/`.

## Wow features (session 2, branch `features-wow`)
- Shipped: policy receipt (page image + boxed quote), what-if income slider, Read it to me (device voice), $0 finale,
  deadline + .ics, optional SNAP/Medicaid/WIC question (+ benefit letter on the packet checklist), state-law box
  (WA, CA, MD, OR, NJ only), appeal letter (`kind: "appeal"` on `POST /api/packet`), charity-care tile map on home.
- Hospital's own form: Fort HealthCare has none as a PDF (its application is an online web form). Marshfield Clinic's is a fillable PDF,
  so the packet for Marshfield now ends with Marshfield's own form (EN fillable, ES as published; `data/forms/`, checksums in
  `sources.json`). We fill only the signature date; its fields don't cover account number, service date or household size, and its
  income boxes are per person and per source, so we don't guess. New dependency: `pypdf` (fills and merges the form).
- **Voice license, decided (Anish, Nov 22):** browser voice. Kokoro's web bundle includes espeak-ng (GPL-3.0), so nothing
  from Kokoro/espeak-ng is vendored and BillBack stays MIT. Read it to me uses speechSynthesis in EN and ES.
- State laws: NY (403), IL (TLS error) and CO (bill summary has no 250% figure) couldn't be confirmed on the official pages, so they're left out.
- 6 of 50 cached policy quotes can't be located on their page (tables, odd text layers): the receipt says
  "We couldn't box this line" and draws no box. LA County, Mercy and Ochsner have no PDF on disk, so the button is hidden.
- Deadline date math tests: `node --test frontend/lib/deadline.test.mjs`.
