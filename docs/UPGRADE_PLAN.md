# Upgrade plan: Global AI Builder's Challenge (Nov 21–28, 2026)

Written 2026-11-23 after reading the repo, before changing code. Each work item from the brief maps to the files it touches.
The `TODO(team)` list for the whole upgrade is at the end of this file.

## What the repo actually is (read before editing)

- **Stack:** FastAPI backend (`backend/`), B's rules engine (`billback/eligibility.py`, plain Python), Next.js 16 front end (`frontend/`),
  deployed on Vercel (`vercel.json`, `api/index.py`). Not Streamlit.
- **AI provider:** **Claude Sonnet 5.5 (`claude-sonnet-5-5`) through the Anthropic API is the default**; Gemini is an optional
  provider behind `LLM_PROVIDER=gemini` (`backend/policy_reader/llm_clients.py`). Only an Anthropic key is configured on the build machine.
- **Already in place:** structured JSON output on every model call; pydantic validation with one retry that includes the validation
  error; per-field `quote` / `page` / `confidence` / `status` on every policy rule; code that checks each quote against the PDF text
  (`backend/policy_reader/validate.py`, normalized + fuzzy ≥ 90); sanity checks; a manual-entry path from the first screen;
  a "My hospital isn't listed" option with a Dollar For link; en/es dictionaries (`frontend/messages/*.json`, typed so a missing
  Spanish key fails the build); an eval suite (`eval/*.py`, `eval/results/`) and 263 passing tests.
- **Not in place:** one-command eval, a Tesseract baseline, repeat-run checks across the full pipeline, a policy answer key verified by
  a person (the 102-row pack in `eval/verify/` has no verified rows yet), an image-quality check, backoff with a total timeout,
  in-memory-only live mode (live reads are written to `cache/policies/`), a live-mode UI (the app only *says* "paste a link"),
  hospital search, a shared status component, a `/states` page, timing panel, AI dev log.

## Deviations from the brief (the repo wins; noted here)

| Brief says | Repo reality / what we do instead |
|---|---|
| Gemini Flash is the AI (A1 "Why Gemini Flash") | The product runs on **Claude Sonnet 5.5**. Method A in the benchmark is the bill reader the app actually ships. The "why" paragraph is written for Claude Sonnet 5.5; the Gemini path stays as an option and is not benchmarked (no Gemini key on the build machine). |
| Temperature 0 + fixed seed on every call | Sonnet 5.5 **rejects** `temperature`/sampling parameters (documented in `llm_clients.py`). We keep structured outputs (JSON schema) on every call and measure repeatability as-is. The Gemini client sets `temperature=0` and `seed=0`. |
| Rules JSON field shape `{value, source_quote, page, confidence}` | The rules JSON schema is the contract with B's engine (CLAUDE.md: change only after telling B). Each field already has `evidence.{quote, page, confidence, status, verified}`. We add a **derived** `grounded` view in the API response with exactly `{value, source_quote, page, confidence, verified, needs_checking, problems}` per field; the cached JSON and B's adapter stay as they are. |
| Sanity ranges 100–600 % FPL, window 30–365 days | Tightened from the repo's 100–1000 % / 30–730 days to the brief's ranges. A violation is flagged and caps confidence, so the engine treats the rule as unresolved (never silently used). |
| "Policy fields correct out of 120" | No answer key verified by a person exists yet. `run_all.py` scores only rows a person marked in `eval/verify/answer_key.csv` and prints "pending" otherwise. Grounding-check precision needs the same key, so it is also pending until rows are verified. We do **not** fill the key from model output. |
| 10 test households "worked out by hand", run "through the real pipeline with cached policies" | B's hand-worked key (`data/answer_key.json`) covers B's 20 *synthetic* policies. We keep that and add `eval/data/households.json`: 10 households, each paired with a sample bill and its *real cached* policy, with the arithmetic written out per household (FPL line, % FPL, the policy threshold). Those expectations were worked out by Claude Code from the policy limits, not by running the engine, and are marked `checked_by: TODO(team)`. |
| Tesseract baseline on every bill | Homebrew on the build Mac belongs to another user account, so Tesseract + Poppler were installed without admin rights with micromamba into `~/.local/ocr` (conda-forge, Tesseract 5.5.4). The baseline ran on all 12 bills. The deployed app does not need Tesseract. |
| Retry with backoff, 30 s total | Bill reads: 3 tries, 30 s total. Policy reads take 8–40 s per call, so they get 3 tries within 120 s. Both values are constants in one place. |
| "Built during the event Nov 23–28" | The project was first built at EvoHacks II (Nov 22). The README keeps that history and adds a dated "Changed during the Global AI Builder's Challenge" list generated from `git log`. |
| Household size over 20 is invalid | API and UI now accept 1–20 (was 1–30 in the API, 1–12 in the UI stepper). |
| `docs/DEVPOST.md` | The root `DEVPOST.md` was written for EvoHacks II. The new draft for this challenge goes in `docs/DEVPOST.md`; the root file is left as history. |

B's engine (`billback/eligibility.py`) is not edited. C's UI is edited because the brief asks for it (shared status component,
live mode, search); every new string goes through `frontend/messages/{en,es}.json`.

## Work items → files

1. **Eval harness** — `eval/run_all.py` (one entry point), `eval/compare.py` (+ `backend/tests/test_compare.py`),
   `eval/data/bills/*.truth.json` (from the existing human answer key `sample_bills/answer_key.csv`, condition tags mapped to
   clean/angled/crumpled/dim/blurry), `eval/data/policies/` (README pointing at `data/policies/` + `eval/verify/answer_key.csv`),
   `eval/data/households.json`, `eval/results/*.json` (timestamp + model), `docs/RESULTS.md` (generated).
2. **Bill reader benchmark** — `eval/bench_bill_reader.py`, `eval/baselines/tesseract_extract.py`, `eval/pricing.py` (the one price
   constant, with source). Method A = Claude Sonnet 5.5 bill reader; Method B = Tesseract + regex/heuristics.
3. **Repeatability** — `eval/repeat_runs.py`: 3 bills × 5 runs, 3 policies × 5 runs (fresh reads, cache off, nothing written to
   `cache/`), and eligibility on each run's output. Any difference is listed field by field.
4. **Engine + e2e tests** — `backend/tests/test_rules_edges.py` (200 % exactly, $1 over, household 1, 8, 9+ increment, zero/missing
   income, free ≤ discount invariant on every cached policy, AK/HI), `backend/tests/test_fpl_official.py` (official 2026 values copied
   into the fixture with the source), `eval/run_households.py`.
5. **Grounded policy reader** — `backend/policy_reader/grounding.py` (derived per-field view), `validate.py` (brief's ranges),
   `reader.py` (in-memory mode, no disk writes), tests in `backend/tests/test_grounding.py`. Report in RESULTS.md.
6. **Live mode end to end** — `backend/policy_reader/fetch.py` (typed failure codes; HTML text fallback),
   `backend/policy_reader/extract_text.py` (empty/encrypted/too-short checks), `backend/live_session.py` (in-memory session store,
   TTL + size cap), `backend/policies.py` (load `live-*` slugs from memory), `backend/app.py` (`POST /api/policy/read` returns a slug,
   `POST /api/policy/manual` for typed-in thresholds), `eval/live_mode_check.py`, `backend/tests/test_live_mode.py`; front end:
   `frontend/components/flow/NotListed.tsx`, `LivePolicyStep.tsx`.
7. **Failure handling** — `backend/bill_reader/quality.py` (Laplacian variance, size), `backend/llm_retry.py` (backoff + total
   timeout), typed error codes in API responses, `backend/tests/test_failures.py` (blur fixture made with Pillow, mocked API errors,
   invalid household input); front end: `ReadingStep.tsx` (unreadable photo → retake / enter by hand), `ManualEntry.tsx` (pre-filled,
   low-confidence highlighted), `QuestionsStep.tsx` (household 1–20 with inline errors).
8. **Hospital not listed** — `GET /api/hospitals/search?q=` (fuzzy over name + aliases + city + state), `HospitalSearch.tsx`,
   `NotListed.tsx`; README "What you need".
9. **Status design system** — `frontend/components/ui/StatusBanner.tsx` (`info | warning | error | success`, `role=alert`/`status`),
   CSS tokens in `globals.css`, replace every `error-text` / `info-text` / `banner` / ad-hoc alert, `frontend/app/states/page.tsx`
   (404 in production unless `NEXT_PUBLIC_SHOW_STATES=1`).
10. **Timing** — `timings` in API responses, `frontend/lib/timings.ts` (in-memory), dev panel on `/states` and with `?dev=1`;
    `eval/manual_timing.csv` (TODO rows) and an auto-filled comparison table in RESULTS.md.
11. **AI dev log** — `docs/AI_DEV_LOG.md`.
12. **Docs** — `README.md`, `docs/DEVPOST.md`.

## API contract for the front end (new or changed)

Errors keep `{"detail": "<message>"}` for old clients and add `{"success": false, "data": null, "error": "<message>", "code": "<code>"}`.
The front end translates by `code`; the English message is a fallback only.

| Route | Change |
|---|---|
| `POST /api/bill/read` | adds `quality: {ok, reasons: ["blurry"\|"too_small"\|"dark"], sharpness, width, height}`, `unreadable: bool` (quality bad, or > 2 fields missing/under 0.5), `timings: {bill_read_s}`. Error codes: `bad_file`, `too_large`, `ai_unavailable` (after retries), `ai_invalid`. |
| `GET /api/hospitals/search?q=` | `[{slug, name, state, city, score}]`, top 8, score ≥ 60 |
| `POST /api/policy/read` | `{url}` JSON or multipart `file` → `{slug: "live-<sha8>", hospital_name, state, rules, grounded: {field: {value, source_quote, page, confidence, verified, needs_checking, problems}}, needs_checking: [field], cached, seconds}`. Error codes: `live_off`, `bad_url`, `fetch_failed`, `fetch_timeout`, `not_pdf`, `no_pdf_link`, `pdf_encrypted`, `pdf_empty`, `too_short`, `too_large`, `ai_unavailable`, `ai_invalid`. |
| `POST /api/policy/manual` | `{hospital_name, state, free_max_percent, discount_max_percent?}` → same shape as above with `slug: "live-manual-<hash>"` |
| `POST /api/eligibility`, `/api/packet`, `/api/policy/thresholds` | accept `live-*` slugs (memory only); `household_size` 1–20; eligibility adds `timings: {rules_s}` |

## Order of work and commits

One commit per item, tests run before and after each: 1 → 2 → 4 → 5 → 7 (backend) → 6 (backend) → 8 (backend) → 3 → front end
(9, then 7/6/8/10 UI) → 10 → 11 → 12. Item 3 runs after the reader changes so its numbers describe the code that ships.

## TODO(team)

Every `TODO(team)` in the repo, in one place. Owner: **A** = AI/backend, **B** = data/rules, **C** = front end.

| # | Owner | What | Where | Why it matters |
|---|---|---|---|---|
| 1 | B | Verify the 102 rows of the policy answer key by reading each PDF (≈20 s per field), and add the 3 missing policies if you can get their PDFs by hand (→ 120 fields). Then run `python eval/run_all.py --offline`. | `eval/verify/index.html` → `eval/verify/answer_key.csv` | "Policy fields correct out of 120" and the grounding check's precision stay **pending** until a person verifies rows. |
| 2 | B | Re-check the 10 end-to-end household expectations by hand and put your name in `checked_by`. | `eval/data/households.json` | They were worked out by Claude Code from the policy limits, not by a person. |
| 3 | B | Decide on E2E-10: an out-of-state household at a hospital with a residency rule gets "we can't tell" from the engine; reading the policy says "probably not eligible". Change the engine or the expectation, with a test. | `billback/eligibility.py` (no-tier-qualified branch), `eval/data/households.json` | The only end-to-end mismatch (9/10). |
| 4 | — | ~~Install Tesseract and run the OCR baseline on all 12 bills~~ **Done** Nov 23 (37/60 vs. the AI's 57/60). | `eval/bench_bill_reader.py` | — |
| 5 | A | One unseen hospital is done (Mad River Community Hospital, CA: read in the app and by `eval/live_mode_check.py`). Fill in the hand-check column for it by reading the PDF, and add 1–2 more links, at least one a web page rather than a PDF. | `eval/live_mode_check.py` (`UNSEEN_POLICY_URLS`) → `eval/results/live_mode_check.csv` | Rubric R2 "demanding example": live mode on an unseen hospital. |
| 6 | A or C | Time yourself finding the 6 fields in 3 policies with a stopwatch. | `eval/manual_timing.csv` | The person-vs-BillBack timing table in RESULTS.md fills itself in. |
| 7 | A | Finalize the "Why Claude Sonnet 5.5" paragraph against the latest numbers. | `docs/RESULTS.md` section 1 (generated from `eval/run_all.py`) | Rubric A1 write-up. |
| 8 | all | Write the team's own AI-assisted development story from the original build weekend. | `docs/AI_DEV_LOG.md` | Rubric A4. |
| 9 | A | Fill in the Devpost answers marked TODO (demo URL, video URL, what each person did this week). | `docs/DEVPOST.md`, `README.md` | Submission. |
| 10 | C | Check the new screens on a phone and with a screen reader (VoiceOver/TalkBack), then capture `/states` for the video (`NEXT_PUBLIC_SHOW_STATES=1` in production). | `frontend/app/states/page.tsx` | Rubric D2; automated checks can't cover a real screen reader. |
| 11 | C | Re-deploy and confirm the deployed demo still works (curated hospital → result → packet, Spanish, live mode on/off as intended). | Vercel | Definition of done: "the deployed demo still works". |
