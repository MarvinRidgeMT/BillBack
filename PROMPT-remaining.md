# Claude Code task: everything left for Person A (Anish), Gate 2 → submission

Read `CLAUDE.md` and `PROMPT-policy-reader.md` first. This file covers ALL remaining Person A work, split into phases.
**Do one phase at a time. At the end of each phase: run the checks, commit, push, and stop and report** (what's done, what isn't, commit hash, anything B or C needs to know). Don't start the next phase until I say "go phase N". If I say "status", tell me which phase we're in and what's left.

Times are ET, Sunday Nov 22, 2026. Submit at 1:30pm (real deadline 3:00pm).

---

## Phase 0: Health check (5 min, do this now)
1. `git status`, `git log --oneline -15`, list the repo tree (2 levels).
2. Report which of these exist and work: `fpl_2026.json`, bill reader, policy reader, B's rules engine + tests, C's UI, `cache/policies/*.json`, `.env.example`, `.gitignore` with `.env`.
3. Run `pytest -q` and report.
4. Check `fpl_2026.json` against the official 2026 HHS poverty guidelines (aspe.hhs.gov/topics/poverty-economic-mobility/poverty-guidelines). Look it up; don't trust memory. It needs the 48 contiguous states plus DC, Alaska and Hawaii, and the per-person add-on for households over 8. Flag any mismatch.
5. Give me a 5-line "what's blocking Gate 2" list, then continue straight into Phase 1 if nothing is blocking.

## Phase 1: Gate 2, due 2:00am
Follow `PROMPT-policy-reader.md` exactly. Gate 2 = the policy reader works on 5 real policies, the JSON is cached, and B's tests pass.
Before stopping:
- Run `superpowers:verification-before-completion`: show real CLI output for all 5 policies.
- Write `NOTES_FOR_TEAM.md` with: the schema as it stands now, anything B must change, and 1–2 failures or oddities found while spot-checking.
- `git push`. I'm going to sleep right after this phase, so **nothing can be left uncommitted.** Print the exact commit hash.

## Phase 2: Live mode, caching and my evals (7:00–9:00am, feature freeze at 9:00)
**2a. Cache all 20 policies**
- `python -m backend.policy_reader.cli --all data/policies/` → 20 JSONs in `cache/policies/`, committed.
- Build `cache/policies/index.json`, which maps hospital name + aliases + city/state to the cache file. Bill → hospital matching uses it.
- Hospital matching: fuzzy-match the bill's extracted hospital name + address against the index (`rapidfuzz` token_set_ratio, plus a state/city check). Return the top match and a score. Below the threshold → tell the UI "not in our list, paste the policy link" (that's live mode).
- **Demo-safe mode:** env `DEMO_CACHE_ONLY=1` makes every endpoint serve only cached results and never call Gemini. We record the video with this on.

**2b. Live mode**
- `POST /api/policy/read` (file or `{url}`) already exists from Phase 1. Harden it:
  - URL fetch: http/https only, block private/localhost IPs (SSRF), follow ≤5 redirects, 20 s timeout, 25 MB cap. If the page is HTML, find the FAP PDF link.
  - Clear error messages the UI can show as-is: "That link isn't a PDF", "This policy is a scanned image; results may be less accurate", "Couldn't reach that site".
  - Return `{ rules, source, seconds, cached: bool, needs_human_review }`.
  - Response includes a `beta: true` flag. The UI labels live mode "beta".
- Coordinate the endpoint contract with C. Put a request/response example in `NOTES_FOR_TEAM.md` and in the README API section.
- Timebox: if live mode isn't solid by 8:30am, leave it behind a feature flag (`LIVE_MODE=0` by default) and move on. The plan says cut live mode first.

**2c. My evals (nobody else owns these, and the judges see them)**
Write `eval/` scripts that print markdown tables I can paste into the README:
- `eval/bill_extraction.py`: run the bill reader on C's 10 sample bill photos against a hand-made `eval/bills_answer_key.csv` (fields: hospital_name, address, amount_due, service_date, account_number). Ask me or C for the true values if the key doesn't exist; don't invent them. Score per field with normalization (amounts to cents, dates to ISO, address fuzzy ≥ 90). Report X/50, broken down by photo condition (flat, angled, crumpled, dim).
- **Low-confidence count:** how many extracted fields came back < 0.8 and were sent to the patient to confirm (bills + policies).
- `eval/speed_cost.py`: average and max seconds per bill, end to end and per stage (bill read, match, policy read cached vs. live, rules, packet). Estimated $ per bill from the token counts in the API response × the current Gemini Flash price (look the price up; cite the page in a comment). Targets are < 60 s and < $0.05.
- `eval/policy_reader.py`: if B's eval script doesn't already do this, score cached policy JSON against B's answer key (`20 policies × 6 fields`) → X/120 with a per-field breakdown and a list of every miss. If B already has one, just run it and collect the output.
- Save all outputs to `eval/results/*.md` and commit.
- Pick the single most instructive failure (e.g. an asset test buried in a footnote) and write it up in 3–4 sentences for the README Limits section.

**Before 9:00am:** `pytest -q` green, the whole flow works locally on one sample bill (cached), push, report the numbers. Send the accuracy numbers to B and C (paste them into `NOTES_FOR_TEAM.md` under "FINAL NUMBERS FOR VIDEO").

**After 9:00am, feature freeze:** bug fixes only. No new features.

## Phase 3: README, Devpost text, repo goes public (9:00am–12:30pm, repo public by 11:30am)
Use `superpowers:writing-plans` for a quick outline, then `humanizer:humanizer` or a plain-language pass so it doesn't read like AI filler. Only claim numbers that exist in `eval/results/`.

**3a. `README.md`** (judges read this, so keep it scannable):
1. **BillBack**: one-line pitch ("You may not owe this bill. BillBack finds out in 60 seconds and fills out the form."), demo link, video link (placeholders until C sends them).
2. **The problem:** nonprofit hospitals billed about $2.7B in a year to patients who likely qualified for charity care (cite KFF Health News: https://kffhealthnews.org/news/patients-eligible-for-charity-care-instead-get-big-bills). Dollar For shows the approach works (17,000+ applications, $60M+ relieved) but reads policies by hand (cite https://pmc.ncbi.nlm.nih.gov/articles/PMC12230784). Verify both links still load.
3. **Who it's for:** uninsured or underinsured low-income patients and the family members who handle their paperwork.
4. **How it works:** the 6-step pipeline (bill reader → hospital match → AI policy reader → patient confirms → rules engine (no AI) → packet PDF). Include a Mermaid diagram.
5. **Results:** the accuracy table (policy fields X/120, bill fields Y/50, households Z/10, unit tests pass count, avg seconds, avg $), plus the low-confidence count.
6. **Appropriate use of AI:** AI extracts; code decides; every value has a quote + page + confidence; < 0.8 → the patient confirms; the patient sends the letter themselves.
7. **Limits:** "likely eligible, not a guarantee"; the honest failure write-up; live mode is beta; scanned PDFs are less accurate; state charity-care laws, EOBs and billing-error detection aren't covered; nothing is stored. Link Dollar For and "call the hospital's billing office."
8. **Run it locally:** exact commands from a fresh clone (Python venv, `pip install -r requirements.txt`, `brew install tesseract poppler`, `cp .env.example .env`, backend + frontend start commands, `pytest`). **Actually test these in a fresh clone in /tmp** and fix anything that breaks.
9. **API:** `/api/bill/read`, `/api/policy/read`, `/api/eligibility`, `/api/packet` with request/response examples (check the real route names).
10. **Data:** list of the 20 hospitals with state, policy URL and download date (from B's `sources.csv`); FPL source; "all bills are fictional."
11. **Built during EvoHacks II:** see 3c.
12. **Team:** A (Anish), B, C and what each built (ask me for names/handles).

**3b. `DEVPOST.md`**: copy-paste-ready text for each Devpost field:
- Project name, tagline (≤ 60 chars), and an "Inspiration / What it does / How we built it / Challenges / Accomplishments / What we learned / What's next" set of sections, each 3–6 sentences, specific, with the real numbers.
- "Built with" tag list.
- Sponsor tools used (only if we actually used MojoAuth/SSOJet/Formaloo; otherwise say none).
- Map it to the judging rubric: fit to the prompt, problem + impact, technical execution, usability + accessibility, appropriate use of tech, video. Each section should give judges proof (numbers, the tests, the Spanish toggle, screen-reader support).

**3c. "Built during the event" statement** (Devpost requires this; missing it risks disqualification):
- List every pre-existing thing we used: libraries (generate from `requirements.txt` + `package.json`, direct deps only), APIs (Gemini), datasets (HHS 2026 poverty guidelines, the 20 public hospital FAPs), fonts/icons if any.
- State that all application code was written during the event, and point to the commit history: first commit timestamp → last commit. Get the real timestamps from `git log --reverse --format='%h %ad %an' | head -1` and `| tail -1`.
- Put it in both the README and `DEVPOST.md`.

**3d. Make the repo public safely (by 11:30am)**
Run `zizi-skills:security-and-hardening` (or do this by hand):
- `git log -p | grep -iE "AIza|api[_-]?key|secret|token"` plus check for any `.env` ever committed. If a key was ever committed: **stop and tell me**. I'll rotate the key in Google AI Studio; rewriting history is my call, not yours.
- No real bills, no personal data, no large junk files (> 10 MB) in the repo.
- `.env.example` present, the LICENSE file (MIT unless the team says otherwise), the README renders on GitHub.
- Then tell me it's ready. **I flip the repo to public myself**; don't change repo visibility or push to anything other than our branch without asking.

## Phase 4: Final checks with the team (12:30–1:30pm)
Write `SUBMIT_CHECKLIST.md` and walk through it with me:
- [ ] Demo link loads in a logged-out/incognito browser and one cached bill works end to end
- [ ] Video is under 3:00, **public** on YouTube/Vimeo, and opens logged out
- [ ] Repo is public and opens logged out; the README numbers match the video numbers
- [ ] Devpost: name, tagline, description, video URL, repo URL, demo URL, built-with tags, team members all added, "built during the event" statement
- [ ] Every result screen says "Likely eligible, not a guarantee"
- [ ] `DEMO_CACHE_ONLY` state is what we want for the judged demo (cached is safer)
- [ ] Final `git push`; tag it `v1.0-submission`
Submit by 1:30pm ET. I click Submit on Devpost myself.

---

## Rules for all phases
- Follow `CLAUDE.md`. AI never decides eligibility. No real patient data. No keys in git.
- Small commits, push at the end of every phase.
- When anything fails twice → `superpowers:systematic-debugging`. Before saying something works → `superpowers:verification-before-completion` with real output.
- Don't edit B's rules engine or C's UI without asking me; write requests in `NOTES_FOR_TEAM.md`.
- Don't post, publish, change repo visibility, or submit anything. Those are mine to do.
- If we're behind schedule, say so right away and propose what to cut (order: nice-to-haves → live mode → Spanish → 10 policies instead of 20). Never cut the tests or the accuracy table.
