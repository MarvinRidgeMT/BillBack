# BillBack — EvoHacks II (Claude Code project memory)

I'm Anish, **Person A (AI + backend)** on a 3-person team. Hard deadline: Devpost submit **1:30pm ET Sunday Nov 22, 2026** (real deadline 3:00pm ET). Every hour counts — ship the simplest thing that passes the next gate.

## What BillBack is
Photo of a hospital bill → filled-in charity-care (financial assistance) application in under a minute.
Pitch: "You may not owe this bill. BillBack finds out in 60 seconds and fills out the form."
Nonprofit hospitals must offer free/discounted care to low-income patients. AI reads the hospital's financial assistance policy (FAP) into rules; **plain code** decides eligibility; the patient confirms everything and sends it themselves.

## Non-negotiable rules
1. **AI never decides eligibility.** AI only extracts (bill fields, policy rules). B's rules engine (plain Python, pytest) makes the call.
2. **Every extracted value carries a confidence score and a verbatim source quote + page number.** Anything < 0.8 confidence goes to the patient to confirm — never used silently.
3. **No real patient data, ever.** Bills are fake. We don't save bills or answers; requests are processed in memory, and the bill image is sent to our AI provider to be read.
4. **No API keys in git.** Keys live in `.env` (gitignored). Ship `.env.example`.
5. Results say "Likely eligible — not a guarantee." Never phrase anything as legal/financial advice.
6. Everything must be built during the event; commit early and often (commit history is our proof).

## Team & ownership
- **A (me):** repo, `fpl_2026.json`, bill reader, **AI policy reader**, live mode + caching, README + Devpost text
- **B:** 20 policy PDFs, **rules engine + pytest**, hand-labeled answer key (20 policies × 6 fields), test households, eval
- **C:** Next.js upload/result UI, sample bill photos, application packet PDF (ReportLab) + Spanish, accessibility, deploy

Don't touch B's rules engine or C's UI without asking. The **rules JSON schema** (below) is the contract between my policy reader and B's engine — change it only after telling B.

## Stack
Python 3.11+, FastAPI, `anthropic` SDK (default: **Claude Sonnet 5.5**, `claude-sonnet-5-5`, structured JSON output; `google-genai`/Gemini optional via `LLM_PROVIDER=gemini`), pdfplumber, pytesseract + pdf2image (scanned PDFs), httpx, pydantic v2, pytest. Front end is Next.js (C). Deploy: Vercel.
Key in `.env` as `ANTHROPIC_API_KEY`; model from `ANTHROPIC_MODEL` (default `claude-sonnet-5-5`), effort from `ANTHROPIC_EFFORT` (default `medium`). Sonnet 5.5 rejects `temperature`, so we don't send it. Gemini (optional): `GEMINI_API_KEY` + `GEMINI_MODEL`, temperature 0.

## Gates (times ET)
- 11:00pm Gate 1 — one bill: photo → fields → hardcoded policy → result on screen
- **2:00am Gate 2 — policy reader turns 5 real policies into rules JSON; B's unit tests pass** ← current target
- 9:00am Gate 3 — feature freeze: deployed, eval run on 20 policies, accuracy table filled
- 11:30am Gate 4 — video recorded, README done, repo public
- 1:30pm — submit on Devpost
If a gate is at risk: cut scope, don't move the gate. Cut order: live mode → Spanish → 20 policies down to 10. Never cut rules-engine tests or the accuracy table.

## Eval targets (what judges see)
- Policy reader: ≥ 90% of 120 fields correct (20 policies × 6 fields)
- Bill extraction: ≥ 90% of 50 fields (10 bills × 5 fields)
- End-to-end: 10/10 test households
- Speed/cost: < 60 s and < $0.05 per bill
Record at least one honest failure for the README "Limits" section.

## Skills to use (if installed in this Claude Code)
- `superpowers:writing-plans` — 10-line plan before starting a multi-file task (keep it short; we're on the clock)
- `superpowers:test-driven-development` — write the test first for schema validation, quote-verification, FPL math, caching
- `superpowers:systematic-debugging` — when anything fails twice, stop guessing and use this
- `superpowers:verification-before-completion` — run it for real before saying a gate passed
- `prompt-design:prompt-design` — when writing/tuning the model prompts
- `anthropic-skills:pdf-reading` — inspecting a policy PDF (scanned vs text, tables)
- `codex-review:code` or `superpowers:requesting-code-review` — quick review before Gate 3 freeze
- `zizi-skills:security-and-hardening` — before the repo goes public (keys, uploads, URL fetching)
If a skill isn't available, just follow its intent and move on — don't stall.

## Working style
- Small commits with clear messages. Push before anyone sleeps (nobody is awake ~3:00–5:30am).
- Prefer boring, working code over clever code. No new dependencies without a reason.
- When unsure about the schema or what B/C expect, write the question in `NOTES_FOR_TEAM.md` and keep going with a sensible default.
