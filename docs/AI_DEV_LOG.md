# AI-assisted development log

How we used AI coding tools while building BillBack, and how a person or a test checked what they produced.
One entry per piece of AI-written work that was checked. Entries are honest: if a check passed the first time, it says so.

## Template

```
### <short title>
- Date:
- Tool: (Claude Code / Copilot / ChatGPT / ...)
- What the AI produced:
- How it was checked: (which test, known answer, or manual check)
- What the check found:
- Decision: kept / changed / rejected, and why
- Commit:
```

---

## Entries from the Global AI Builder's Challenge upgrade (Nov 23, 2026, Claude Code)

### 1. Free-care vs. discount invariant test caught a real policy that breaks it
- Date: 2026-11-23
- Tool: Claude Code (Claude Opus 5.5)
- What the AI produced: `backend/tests/test_rules_edges.py::test_free_limit_never_above_discount_limit`, which asserted that
  every cached policy's free-care limit is at or below its discount limit and every discount tier's upper limit.
- How it was checked: ran `pytest` against all 22 cached real policies.
- What the check found: it **failed** on Novant Health: free care up to 300% of the poverty line (for uninsured patients) but
  discount tiers that stop at 250% and 300% (for insured North Carolina residents). Our rules schema has one free-care
  limit, so it can't say "300% if uninsured, 200% if insured". The reader had already flagged both fields for human
  review and written a warning, but the code's sanity check only compared the free limit with the *overall* discount
  limit, not with each tier.
- Decision: **changed**, two things. (1) The test now requires "invariant holds, or the policy is flagged for review",
  which is the real safety property (never used silently). (2) Added a plain-code sanity check for "free limit above a
  tier's upper limit" (`backend/policy_reader/validate.py`) so this is flagged by code, not only by the model's own
  warning; re-ran code validation on Novant's saved output (no model call), which capped its confidence 0.7 → 0.6.
- Commits: `79bbf02` (test), `2c2aa87` (sanity check + Novant re-check)

### 2. Re-running validation silently changed every policy's download date
- Date: 2026-11-23
- Tool: Claude Code
- What the AI produced: tightened sanity ranges and re-ran code validation on all cached policies
  (`python -m backend.policy_reader.cli --revalidate data/policies/`).
- How it was checked: read the `git diff` of `cache/policies/` before committing.
- What the check found: 19 files changed, but only Novant should have. `revalidate_cached` rebuilt each policy's
  `source` with **today's date** as `retrieved_at`, so every policy now claimed it was downloaded on Nov 23 (they were
  downloaded Nov 22). Wrong provenance, a quiet bug that tests didn't cover.
- Decision: **changed**. Reverted the cache files, made revalidation keep the original download date, re-ran: only
  Novant changed.
- Commit: `2c2aa87`

### 3. Hospital search matched the wrong hospital on a shared word
- Date: 2026-11-23
- Tool: Claude Code
- What the AI produced: `search_hospitals()` using rapidfuzz `WRatio` over name, aliases, city and state.
- How it was checked: probed with known answers, including hospitals we do NOT have ("Mayo Clinic", "St Jude").
- What the check found: "Mayo Clinic" matched Marshfield Clinic at 85/100 and "children colorado" matched an Illinois
  system at 85/100. For "my hospital isn't listed", a confident wrong match is worse than no match.
- Decision: **changed**. Every word of the query must now fuzzily match a word in the hospital's names, city or state
  before it can score above the cut-off. "Mayo Clinic" now returns nothing; typos ("marshfeld") and cities ("Mobile")
  still work. Both cases are now tests (`test_search_does_not_match_a_different_hospital_on_a_shared_word`).
- Commit: `a2c4d0d`

### 4. A test failure that was the code being right (kept as a test)
- Date: 2026-11-23
- Tool: Claude Code
- What the AI produced: the live-mode end-to-end test, with a fake policy PDF and a mocked model.
- How it was checked: `pytest backend/tests/test_live_mode.py`.
- What the check found: the test expected "likely free" and got "we can't tell". The fake PDF didn't contain the
  model's quotes for the savings and residency rules, so the grounding check marked them unverified and the engine
  refused to treat them as a pass. That is exactly the intended behavior; the **test** was wrong.
- Decision: **kept the code, changed the test** to build the fake policy from the quoted sentences, and **added** the
  original situation as its own test (`test_quote_missing_from_the_pdf_needs_checking_and_is_never_a_pass`).
- Commit: `a2c4d0d`

### 5. End-to-end households: one real mismatch, reported instead of fixed to pass
- Date: 2026-11-23
- Tool: Claude Code
- What the AI produced: 10 end-to-end households (`eval/data/households.json`) with expected results worked out from the
  policy limits (arithmetic written per household), and `eval/run_households.py`.
- How it was checked: ran the real pipeline (saved sample-bill read → match → cached policy → rules engine → packet).
- What the check found: 9/10. E2E-10 is a Texas household at Fort HealthCare (Wisconsin), whose policy limits
  assistance to its service area: by hand, "probably not eligible"; the engine says "we can't tell". The engine is
  conservative (it never says free), but it isn't the hand answer.
- Decision: **kept as a reported mismatch**. B owns the engine, so it wasn't edited to make the number 10/10;
  `TODO(team, B)` in `docs/UPGRADE_PLAN.md`. Expectations still need a person to re-check them (`checked_by` is a TODO).
- Commit: `79bbf02`

### 6. Two of my own tests were wrong (the code was right)
- Date: 2026-11-23
- Tool: Claude Code
- What the AI produced: `test_free_above_one_tier_top_is_flagged` (grounding) used a free limit of 300%, which is not
  above the fixture's 300% tier, so it could never trigger.
- How it was checked: it failed on the first run; reading the fixture showed the test's numbers were wrong.
- Decision: **changed the test** to 350% (above one tier's top, under the overall 400% limit).
- Commit: `2c2aa87`

### 7. Repeat runs gave a patient two different answers; fixed in the prompt
- Date: 2026-11-23
- Tool: Claude Code
- What the AI produced: `eval/repeat_runs.py` (3 policies × 5 fresh reads, eligibility on each) and, after it failed,
  three new rules in `backend/prompts/policy_reader.md`.
- How it was checked: the repeat-run eval itself, run twice (before and after the prompt change), ~$0.65 per run.
- What the check found: for Marshfield Clinic, **eligibility differed in 2 of 5 runs** (the same household came back
  "likely free" or "we can't tell"). The residency rule flipped between "stated" and "unclear" because the policy waives
  it for emergencies, and the prompt had no rule for conditional requirements. Fort's discount table came back as one or
  two "sliding scale" bands. Claude Sonnet 5.5 takes no temperature or seed, so the fix had to be removing the ambiguity.
- Decision: **changed the prompt** (conditional rules are "stated" with the exception in a warning; asset words outside
  an asset section are not an asset test; merge bands only when type and value match). After: eligibility identical in
  15 of 15 runs; one informational field (`income_basis`) still varies on Marshfield and is reported, not hidden. The 22
  cached policies were read with the earlier prompt and were not re-read.
- Commit: `bb0e0a0`

### 8. The new retry code could still fail on one slow call
- Date: 2026-11-23
- Tool: Claude Code
- What the AI produced: `backend/llm_retry.py` (3 tries, exponential backoff, 30 s total budget for bills), with tests.
- How it was checked: unit tests passed; then the live bill benchmark.
- What the check found: one bill (a text PDF that normally reads in 2–4 s) failed with "timed out after retries". The
  first try had been given the whole 30 s budget, so a single hung call left no time for the promised retries. The unit
  tests didn't catch it because the fake client never hung.
- Decision: **changed**: each try is capped (12 s for bills, 60 s for policies), and a regression test checks the cap.
  The benchmark was re-run after the fix.
- Commit: `960fd30`

### 9. An independent review of this week's backend found security and eval problems the tests didn't
- Date: 2026-11-23
- Tool: Claude Code (a separate reviewer agent given only the diff, not the author's reasoning)
- What the AI produced: the week's backend and eval changes (items 1–8).
- How it was checked: code review of `git diff 3cd2138..HEAD -- backend eval`, then each finding checked by hand.
- What the check found (all confirmed): live-mode link fetching could be pointed at a private address by a second DNS
  answer (DNS rebinding); a server sending one byte at a time could hold a worker for hours; uploads over 1 MB were
  spooled to a temp file on disk, which contradicted "nothing is stored"; 8-character live slugs; a search query of
  two apostrophes crashed the endpoint; and the address comparison counted "123 Main St" vs "125 Main St" as correct.
- Decision: **changed**, each with a test: connect to the checked IP (Host + TLS SNI kept), 45 s wall-clock fetch
  limit, uploads kept in memory and oversized requests refused before parsing, 16-character slugs plus a per-client
  rate limit, a guard for empty searches, and addresses must match on every number. Re-scoring the saved bill reads
  with the stricter address rule left the result at 57/60 (no hidden inflation).
- Commit: `368bbb8`

### 10. Clicking through the real app caught wording the unit tests passed
- Date: 2026-11-23
- Tool: Claude Code (front end written by a sub-agent; checked in the browser by the main session)
- What the AI produced: the live-policy screen that explains each rule in plain words.
- How it was checked: ran the real backend and clicked through "my hospital isn't listed" with a policy we had never
  read (Mad River Community Hospital, CA, found by web search), plus the happy path in English and Spanish and a
  simulated AI outage.
- What the check found: everything worked end to end (read in 8.1 s, result, application PDF, nothing on disk), but
  "Time to apply" said "Found in the policy" and then "The policy doesn't say", because the policy states there is
  *no* deadline and the code treated "no number of days" as "not stated".
- Decision: **changed**: a stated deadline without a number now says to read the policy's own words, with a test from
  this exact case. Also fixed a misleading "retrying in 4.0s" log line on the last try, seen in the outage test.
- Commit: `537cd5d`

### 11. Keeping the OCR baseline fair instead of easy to beat
- Date: 2026-11-23
- Tool: Claude Code
- What the AI produced: the Tesseract + rules baseline (`eval/baselines/tesseract_extract.py`), Method B in the bill
  benchmark the AI is compared against.
- How it was checked: once Tesseract was installed, ran it on all 12 bills and read every miss next to the OCR text.
- What the check found: first run 32/60. Most misses were real OCR errors (zeros read as nines), but some were the
  baseline's own fault: on the *clean* bill it took a line item instead of AMOUNT DUE because the "please pay"
  sentence matched first; the OCR mode that splits columns was preferred over the one that keeps label and number on
  one row; OCR money like "$4 931-80" and em-dashes weren't cleaned up. Reporting 32/60 would have overstated the AI's lead.
- Decision: **changed the baseline** (label priority, row-keeping OCR mode first, money/dash cleanup), with unit tests
  from the real OCR strings; re-ran: 37/60. Tuning on the same bills favors the baseline, so RESULTS.md says the gap is,
  if anything, understated. Also added "wrong values returned" to the report: baseline 15, AI 0.
- Commit: `01fc4b1`

### 12. Graphify's automated PR review found five more bugs
- Date: 2026-11-23
- Tool: Graphify PR review on PR #1 (gate passed, 0 blocking; its investigation listed 5 bugs and did not finish), fixes by Claude Code
- What the AI produced: the PR's backend, eval and front-end code.
- How it was checked: each finding reproduced or read against the code before changing anything; a test written first.
- What the check found (all 5 confirmed): a chunked upload with no Content-Length skipped the size cap and could spool a
  large file to disk; the Gemini client accepted the per-try timeout but ignored it; OCR money split across two lines
  crashed the baseline with a ValueError; one unimportable eval module aborted `run_all.py` before RESULTS.md was
  written; and going back from "my hospital isn't listed" with a different hospital's bill kept the first hospital's
  name and state for the policy check.
- Decision: **changed**, each with a regression test: a streaming body-size cap (counts bytes as they arrive), the
  timeout passed to the Gemini SDK, OCR money matched within one line, eval modules imported per step, and a fresh
  not-listed draft whenever the bill's hospital changes. Re-ran the baseline: still 37/60.
- Commit: see the commit after `c01e620` ("fix: five bugs from Graphify's review of PR #1")

---

## The team's own story from the original build weekend

### TODO(team): your entry
- Date: TODO(team)
- Tool: TODO(team)
- What the AI produced: TODO(team)
- How it was checked: TODO(team)
- What the check found: TODO(team)
- Decision: TODO(team)
- Commit: TODO(team)

Ideas from the repo history you could write up (check them against your memory first): the bill reader logging bill
values on invalid output (`f358599`), the six-policy answer key that turned out to be AI-written and was moved to a
cross-check (`32079c8`, `be04502`), the Adena asset-test-from-a-form-checkbox read (README "Limits").
