# Claude Code: FINAL PUSH, everything unfinished (Sun Nov 22, 2026)

Read `CLAUDE.md` and `NOTES_FOR_TEAM.md` first. This replaces `PROMPT-remaining.md`.

## Timeline (ET), hard stops
| Time | Checkpoint |
|---|---|
| now → **11:45** | Part 1: merge all branches, real eligibility engine, full flow works, deployed |
| 11:45 → **12:15** | Part 2: accuracy numbers |
| 12:15 → **12:30** | Part 3: demo-ready check. **Video recording starts 12:30**; freeze the demo |
| 12:30 → **1:45** | Part 4: README, DEVPOST.md, "built during the event" statement, security pass |
| 1:45 → **2:15** | Part 5: final checks. Anish makes the repo public and submits. **Real Devpost deadline: 3:00pm ET** |

At each checkpoint: `pytest -q` green → commit → `git push origin main` → report in under 10 lines (done / not done / commit hash / anything B or C must do). Then continue to the next part **without waiting**, unless something is blocked.

**From 12:30 on, don't change anything that affects what's on screen** (UI, API responses, cached data) unless Anish asks. B and C are recording. Docs, evals and tests are fine.

Skills: `superpowers:systematic-debugging` when anything fails twice; `superpowers:verification-before-completion` before every report (show real output); `codex-review:code` or `superpowers:requesting-code-review` on the merge diff if there's time; `zizi-skills:security-and-hardening` in Part 4; `humanizer:humanizer` on the README/Devpost text. If a skill isn't installed, follow its intent and keep going.

## Current state (verified 10:51am)
- `main` (A): policy reader, 6 cached real policies, bill reader, `backend/fpl.py`, `eligibility_stub.py`, `/api/policy/read`, `/api/bill/read`, `/api/eligibility`, `backend/e2e_cli.py`. 87 tests passing.
- **`data/fpl_2026.json` was just added (real 2026 HHS numbers, from the Federal Register 2026-00755) and is NOT committed yet.** Commit it first.
- `origin/person-b-eligibility` (B): `billback/eligibility.py` (EligibilityEngine, HospitalPolicy, AssistanceTier, PolicyCondition, FPLGuideline, PovertyGuidelineResolver), `billback/scorer.py`, `scripts/evaluate.py` (has `dict_to_policy` at ~line 35), `scripts/independent_households.py`, `data/answer_key.json`, `data/households/HH-*.json`, `data/household_manifest.json`, 20 synthetic + 20 real policies, `PERSON_B_HANDOFF.md`. Their demo still uses the **2024 synthetic FPL resolver**, and the FPL evidence has `year: null`.
- `origin/frontend-ui` (C): Next.js app (upload → reading/confirm → manual entry → questions → result) with an `/api` rewrite, plus 10 fake sample bills + an answer key.
- Not done: merging, real engine wired in, hospital matching, evals, README, DEVPOST.md, deploy (unknown), packet PDF (unknown), Spanish (unknown).

---

## Part 1: Merge and integrate (stop at 11:45)
1. `git add data/fpl_2026.json && git commit -m "data: real 2026 HHS poverty guidelines"`.
2. `git fetch --all`. Merge `origin/person-b-eligibility`, then `origin/frontend-ui`, into `main` (no squash, so the commit history shows who built what).
   - Conflicts: B owns `billback/`, `scripts/` and B's `data/` files; C owns `frontend/` and the sample bills; A owns `backend/`. For shared files (`NOTES_FOR_TEAM.md`, `README.md`, `.gitignore`, `requirements.txt`) combine both sides.
   - B's handoff uses Windows/PowerShell paths. Make sure everything runs on macOS.
3. **Inventory:** list what C's frontend actually has. Packet PDF download? Spanish toggle? "Likely eligible, not a guarantee" on the result screen? Low-confidence confirm step? Policy quote + source link on the result? Report gaps; don't build big new UI.
4. **Wire B's real engine in place of the stub:**
   - `backend/adapters/policy_to_engine.py`: convert our `PolicyRules` JSON (cache/policies/*.json) → B's `HospitalPolicy` / `AssistanceTier` / `PolicyCondition`. Start from B's `dict_to_policy`.
     - free_care.fpl_max_percent → a "free" tier, threshold_type fpl_percentage, **inclusive**
     - discount.tiers → "discount" tiers with each tier's discount_percent / description, inclusive upper bounds, as the policy wrote them
     - asset_test / residency → PolicyConditions; `status: not_stated` → no condition; `unclear` or < 0.8 confidence → the engine reports it as a missing/unresolved fact, not as a pass
     - source_ref = "Page N" + the quote + the source URL
     - `uses_income_table: true` with no fpl percent → the engine returns cannot_determine and explains why
   - Make B's engine use **`data/fpl_2026.json`, year 2026**. Build `FPLGuideline` objects from our table format, or reuse `backend/fpl.py`. Remove the 2024 synthetic resolver from the live path (tests may keep it).
   - Fix B's bug: the FPL evidence must report the year actually used (2026), not `null`. Add a regression test.
   - `POST /api/eligibility` now calls B's engine. Keep the response keys C's UI already uses: `status` (likely_free / likely_discounted / probably_not_eligible / cannot_determine), the matched tier, evidence (quote, page, source URL, verified), missing facts/caveats, and `disclaimer: "Likely eligible, not a guarantee."` If C's UI expects different keys, adapt the API, not the UI.
   - Delete `eligibility_stub.py` once nothing imports it.
   - Tests: household of 2 at exactly 200% in OH (income $43,280) → likely_free; $43,281 → discounted (for a 200/400 policy); household of 1 and of 9 (add-on); AK and HI; missing income → error; every cached real policy loads through the adapter without crashing.
5. **Hospital matching:** `cache/policies/index.json` (slug, hospital name, aliases, city, state, file). `match_hospital(name, address)` uses rapidfuzz token_set_ratio plus a state check, and returns the top match + score. Below 80 → "not in our list" (the UI shows manual hospital pick / paste a policy link). Add an `index.json` entry for each cached policy. If C's fake bills use made-up hospitals, map them to real cached policies in a `demo_aliases` section so the demo flow matches.
6. **More real policies (only if Part 1 is otherwise done by 11:30):** run the policy reader on B's real policy PDFs that aren't cached yet (`cli --all`; ~$0.04 each). Commit the JSON. Don't block on this.
7. **Demo-safe mode:** `DEMO_CACHE_ONLY=1` → no live LLM calls for policies; bills still go through the bill reader. As a backup, keep a cached bill-reader result for each of C's 10 fake bills (keyed by sha256), so the video can run with no API at all. **Live mode:** if `/api/policy/read` with a URL works on one real hospital URL now, keep it and label it `beta: true`; otherwise put it behind `LIVE_MODE=0` and move on.
8. **Run it for real:** start the backend (uvicorn) and the frontend (`npm run dev` in C's folder). Push one of C's fake bills through upload → confirm → household questions → result → packet (if it exists). Paste the terminal output and the API JSON. Fix only what breaks.
9. **Deploy:** check how C planned to deploy (README/handoff, vercel.json). If a deploy config exists, make sure the backend URL/env is right and tell Anish the exact commands to run (`vercel --prod` etc.). Don't create accounts or projects yourself. If deploy is out of reach, write clean local-run instructions instead; Devpost accepts that.
10. Push. Report.

---

## Part 2: Accuracy numbers (11:45 → 12:15)
Scripts in `eval/`, results as markdown tables in `eval/results/`. Commit both. **Never invent or round in our favor.** Every number must come from a script run.
1. **Bill extraction:** `eval/bill_extraction.py` runs the bill reader on C's 10 fake bills against C's answer key (hospital name, address, amount due, service date, account number). Normalize (amounts to cents, dates to ISO, case/whitespace, address fuzzy ≥ 90). Output X/50, per field, and per photo condition (flat / angled / crumpled / dim, if C labeled them). List every miss.
2. **Policy reader:** use B's scorer/answer key. Check which policies `data/answer_key.json` covers.
   - If it covers real policies we've cached → score our reader on them: X/(N×6), per field, every miss listed.
   - If it only covers B's synthetic policies → run the reader on the synthetic policy files if they're PDFs/text, and score those. Separately, report the hand spot-checks on real policies from NOTES_FOR_TEAM.md (Boys Town 6/6, USA Health 5/6). Label clearly which is which.
   - Apply the `null`-vs-`false` "not stated" mapping from `backend/eval_config.py` and say which one you used.
3. **End-to-end households:** run B's 10 households (`data/households/`) through adapter + engine + 2026 FPL. Compare to B's expected answers → X/10. **Watch out:** if B worked out the expected answers with 2024 FPL numbers, flag every household whose answer changes under 2026 and ask B. Don't silently "fix" the answer key.
4. **Rules engine tests:** total pytest count, passing count, and the specific boundary tests (exactly 200%, $1 over, household of 1, household of 8+, missing income).
5. **Speed and cost:** average and max seconds per bill, end to end and per stage (bill read / match / policy read cached vs. live / eligibility). Cost per bill from the token counts × Claude Sonnet 5.5's price (already cited in the repo). Targets are < 60 s and < $0.05.
6. **Low-confidence count:** how many bill fields and policy fields came in under 0.8 and went to the patient to confirm.
7. Write `eval/results/SUMMARY.md`: one table with Test | Measured | Target | Result, plus 3 sentences in plain language.
8. **Copy the summary table into `NOTES_FOR_TEAM.md` under "FINAL NUMBERS FOR VIDEO"** so B and C read the right numbers in the 1:55–2:25 narration. Push and report the numbers to Anish right away. **They're needed before 12:30.**

## Part 3: Demo-ready check (12:15 → 12:30), then freeze
Run through this and fix only blockers:
- [ ] Cached flow works start to finish on the bill the video will use (ask Anish which one; default: the crumpled one)
- [ ] At least one field shows the "please confirm" low-confidence step (the script points it out)
- [ ] The result screen shows: status, the exact policy quote + page, a source PDF link, "Likely eligible, not a guarantee", and a link to Dollar For / the hospital billing office
- [ ] Packet PDF downloads (if built) with the account number filled in; the Spanish toggle works (if built)
- [ ] Live mode either works on one URL (label "beta") or is hidden
- [ ] `pytest -q` passes; the run is ready to show on screen (`pytest -v` for the video's test-suite shot)
- [ ] A simple architecture diagram exists for the video: `docs/architecture.md` (Mermaid) and, if possible, `docs/architecture.png`
- [ ] Commit, push, tag `demo-freeze`. Tell Anish "ready to record" plus the exact commands to start backend and frontend.

---

## Part 4: README, Devpost and security (12:30 → 1:45; docs only, don't touch the demo)
Only use numbers from `eval/results/SUMMARY.md`. Run `humanizer:humanizer` (or a plain-language pass) at the end so it doesn't read like AI filler.

**`README.md`**
1. **BillBack**: the pitch line ("You may not owe this bill. BillBack finds out in 60 seconds and fills out the form."), demo link, video link (placeholders: `TODO_VIDEO_URL`, `TODO_DEMO_URL`).
2. **The problem:** nonprofit hospitals billed about $2.7B in a year to patients who likely qualified for charity care ([KFF Health News](https://kffhealthnews.org/news/patients-eligible-for-charity-care-instead-get-big-bills)). Dollar For: 17,000+ applications, $60M+ relieved, policies read by hand ([PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC12230784)). Open both links to confirm they load.
3. **Who it's for:** uninsured or underinsured low-income patients and the family members who handle their paperwork.
4. **How it works:** the 6-step pipeline with the Mermaid diagram (bill reader → hospital match → AI policy reader → patient confirms → rules engine, no AI → packet).
5. **Results:** the SUMMARY table + the low-confidence count.
6. **Responsible use of AI:** AI only extracts; plain code decides; every value has quote + page + confidence + verification; < 0.8 → the patient confirms; the patient sends the letter themselves; nothing is stored.
7. **Limits (honest):** "likely, not a guarantee"; the USA Health contradictory application window; the Adena asset test from a form checkbox; watermark text noise; scanned PDFs (no OCR on our build machine → sent as raw PDF, quotes unverifiable); every policy we tested used 200%/400% (no non-standard ones tested); live mode is beta; not covered: state charity-care laws, insurance statements (EOBs), billing-error detection. Link Dollar For and "call the hospital's billing office".
8. **Run it locally:** exact macOS commands from a fresh clone (venv, `pip install -r requirements.txt`, optional `brew install tesseract poppler`, `cp .env.example .env` + `ANTHROPIC_API_KEY`, `DEMO_CACHE_ONLY=1`, backend + frontend start commands, `pytest`). **Test these in a fresh clone in `/tmp`** and fix what breaks.
9. **API:** each route with a request/response example (real route names).
10. **Data:** the hospitals (name, state, policy URL, download date, from `sources.csv` and B's list); 2026 HHS poverty guidelines (Federal Register 2026-00755); "all bills and households are fictional".
11. **Built during EvoHacks II:** see below.
12. **Team:** Anish (A): AI + backend, policy reader, bill reader, FPL, integration. B: eligibility engine, policies, answer key, households, eval. C: front end, sample bills, design, video. Ask Anish for real names/GitHub handles; leave `TODO_NAME` until then.

**`DEVPOST.md`**, copy-paste-ready for each Devpost field: name, tagline (≤ 60 chars), Inspiration / What it does / How we built it / Challenges / Accomplishments / What we learned / What's next (3–6 specific sentences each, with real numbers), "Built with" tags, sponsor tools (none unless actually used).
- If `~/BillBack-research/devpost-whats-next.md` exists (Codex research), use its verified stats and "What's next" text. Keep only claims that have a source URL.
- At the end, add a short "How we meet the judging criteria" map: fit to the prompt, problem + impact, technical execution, usability + accessibility, appropriate use of tech, video.

**"Built during the event" statement** (Devpost requires it; missing it risks disqualification). Put it in both the README and DEVPOST.md:
- Pre-existing things we used: direct dependencies from `requirements.txt` and `frontend/package.json`, the Anthropic Claude API (and the Google Gemini SDK if still in requirements), datasets (2026 HHS poverty guidelines, public hospital financial assistance policies), fonts/icons from C's app.
- All application code was written during the event. Proof: commit history from the first commit to the last. Get the real timestamps with `git log --reverse --format='%h %ad %an' --date=iso | head -1` and `git log -1 --format='%h %ad %an' --date=iso`.

**Security pass before the repo goes public** (`zizi-skills:security-and-hardening`):
- `git log -p --all | grep -nE "sk-ant-|AIza|api[_-]?key\s*=\s*['\"][A-Za-z0-9]"` must find no real keys. **If a key was ever committed: STOP and tell Anish.** He rotates it; you don't rewrite history without asking.
- `.env` never tracked; `.env.example` complete (ANTHROPIC_API_KEY, LLM_PROVIDER, GEMINI_*, DEMO_CACHE_ONLY, LIVE_MODE).
- No real bills or personal data; no files over 10 MB; no `.venv`/`node_modules`/`.next` committed.
- URL fetching blocks localhost/private IPs; uploads have a size cap; nothing is written to disk.
- Add a LICENSE (MIT) if missing.
- Remove or move the internal prompt files (`PROMPT-*.md`, `PLAN-*.md`) into `docs/process/`, and mention that Claude Code helped build it in the "built with" list. Being open about AI-assisted development is better than hiding it.
- Push. Report "ready to go public".

---

## Part 5: Final checks (1:45 → 2:15)
Write `SUBMIT_CHECKLIST.md` and walk through it with Anish:
- [ ] Anish made the repo public; it opens in a logged-out/incognito browser; the README renders and its numbers match the video
- [ ] Demo link works logged out, or the local-run steps work from a fresh clone
- [ ] Video is under 3:00, uploaded **public** (YouTube/Vimeo), opens logged out; `TODO_VIDEO_URL` / `TODO_DEMO_URL` replaced in the README and DEVPOST.md
- [ ] Devpost fields filled from DEVPOST.md: name, tagline, description, video URL, repo URL, demo URL, built-with tags, all 3 team members added, "built during the event" statement
- [ ] Final `git push`; tag `v1.0-submission`
- [ ] **Anish clicks Submit by 2:15pm ET** (hard deadline 3:00pm ET)

## Cut order if behind
1. More real policies (Part 1 step 6) → 2. Live mode → 3. Deploy (use local-run instructions) → 4. Speed/cost per-stage breakdown (keep the totals).
**Never cut:** the merged, working cached flow; the rules engine tests; the accuracy table; the "built during the event" statement.

## Rules
- Follow `CLAUDE.md`: AI never decides eligibility; no real patient data; no keys in git.
- Don't rewrite B's engine logic or redesign C's UI. Adapt with adapters and API shape. Write requests to them in `NOTES_FOR_TEAM.md`.
- Don't change repo visibility, deploy to production, post, or submit. Those are Anish's to do. Give him the exact commands.
- If something will miss its checkpoint, say so right away and propose what to cut.
