# Codex product-expansion plan

**Branch/worktree:** `codex/expansion` in `~/BillBack-codex`  
**Guardrails:** AI extracts only; deterministic code compares/decides; uploads and case state stay in memory; low-confidence values require confirmation; user-facing copy is localized; no edits to Claude Code's evaluation/rubric work.

## F1 — Insurance statement (EOB) reconciliation

- **Add:** `backend/eob_reader/{schema,reader,compare}.py`, `backend/prompts/eob_reader.md`, `backend/tests/test_eob_*.py`, fictional EOB fixtures and `frontend/components/flow/Insurance*` components.
- **Small shared insertions:** `backend/app.py`, `frontend/lib/{types,api}.ts`, `Flow.tsx`, `UploadStep.tsx`, `ResultStep.tsx`, `en.json`, `es.json`.
- **API:** `POST /api/eob/read` (multipart `file`) returns structured fields/claims, confidence, location, and `fields_to_confirm`; `POST /api/eob/compare` accepts confirmed bill + confirmed EOB and returns deterministic discrepancy records with both source values; `POST /api/eob/letter` returns an in-memory EN/ES PDF for `itemized_bill` or `billing_hold`.
- **Tests:** strict schema/privacy, one retry on invalid JSON, confidence threshold, amount/date normalization, exact/rounded/missing/multiple-claim comparison, denial/pending/adjustment/duplicate/itemization flags, EN/ES PDFs, no writes.
- **Risks:** false accusations and bad matching. Call findings “discrepancies,” show both sources, require confirmation below 0.8, and never change charity-care eligibility.
- **Video:** upload the fictional bill plus discrepancy EOB, confirm one low-confidence field, and show the side-by-side discrepancy and letters. Supports **Multimodal AI** and **Health & Wellness**.

## F2 — Plain-language and accessibility pack

- **Add:** `frontend/components/accessibility/{AccessibilityToolbar,GlossaryText,SpeakPanel}.tsx`, `frontend/lib/glossary.ts`, accessibility tests, `docs/ACCESSIBILITY.md`.
- **Small shared insertions:** `Flow.tsx`, `ReadingStep.tsx`, `QuestionsStep.tsx`, `ResultStep.tsx`, `globals.css`, `en.json`, `es.json`.
- **Contract/state:** easy-read and spoken-line state live only in React memory; glossary is static human-written EN/ES; browser `speechSynthesis` only.
- **Tests:** keyboard behavior, glossary rendering, easy-read class, 44px target CSS, 200%/390px Playwright screenshots, axe serious/critical counts in both languages.
- **Risks:** browser voices vary and tooltips can be inaccessible. Always show readable text, use buttons plus named dialogs/details, never autoplay, and preserve visible focus.
- **Video:** toggle easy-read, open a deductible definition, then read the questions/confirmation with sentence highlighting. Supports **Accessibility**.

## F3 — Responsible language expansion

- **Add:** `frontend/messages/vi.json`, `zh-CN.json`, `tl.json`, `frontend/components/LanguageMenu.tsx`, documentation citations/review status.
- **Small shared insertions:** `frontend/lib/i18n.ts`, `Nav.tsx`, `en.json`, `es.json`.
- **Contract:** UI language becomes `en | es | vi | zh-CN | tl`; generated letters remain EN/ES and the UI states that limitation. Machine-translated locales display a persistent review warning.
- **Tests:** identical key sets, language menu keyboard labels, `lang` attribute changes, EN/ES packet routing from non-letter locales.
- **Risks:** unreviewed translations. Mark all three as AI-translated, add `TODO(team)` for human review, and link to the IRS translation-rule source in docs.
- **Video:** switch from English to Vietnamese, show the translation notice and official-language-policy note. Supports **Accessibility** and **Community Impact**.

## F4 — IRS Schedule H cross-check badge

- **Add:** `scripts/schedule_h_crosscheck.py`, `data/schedule_h.json`, parser tests/fixtures, `backend/schedule_h.py`, `frontend/components/flow/ScheduleHBadge.tsx`.
- **Small shared insertions:** `backend/app.py`, `ResultStep.tsx`, `frontend/lib/api.ts`, messages.
- **API:** `GET /api/schedule-h/{hospital_slug}` returns agreement/conflict/unknown, filing tax period, filing URL, XML paths, and reported thresholds; it never changes the eligibility result.
- **Tests:** schema-year tag variants, `000`/blank handling, agreement/conflict/no-match, safe URLs, stale-filing wording.
- **Risks:** EIN/facility mismatches and stale filings. Never guess; commit source URLs, retrieval date, XML path, and omit the badge on uncertainty.
- **Video:** show an agreement badge, open its filing metadata, and say the live policy still controls the result. Supports **Community Impact** and trust.

## F5 — Navigator mode

- **Add:** `frontend/components/navigator/{NavigatorToggle,CaseList,CaseSummary}.tsx`, `frontend/lib/navigator.ts`, client-side zip tests.
- **Small shared insertions:** `Flow.tsx`, `ResultStep.tsx`, messages, CSS, optional MIT `fflate` dependency after license verification.
- **Contract/state:** cases exist only in tab memory; status is `started | result | packet_downloaded`; download-all creates a client-side zip of packet/summary/ICS blobs.
- **Tests:** tab-memory lifecycle, several cases, status transitions, zip contents, EN/ES one-page summaries, no storage APIs.
- **Risks:** accidental persistence and mixed cases. Ban `localStorage`/IndexedDB, show the close-tab warning, label every file, and require downloading before closure.
- **Video:** enable “I’m helping someone else,” complete two fictional cases, then download all. Supports **Community Impact**.

## F6 — Follow-up kit

- **Add:** `backend/follow_up.py`, tests, `frontend/components/flow/FollowUpKit.tsx`.
- **Small shared insertions:** `backend/app.py`, `ResultStep.tsx`, messages.
- **API:** `POST /api/follow-up` returns an in-memory EN/ES PDF for `status_request`, `more_documents`, or `eca_pause_request`; inputs are bounded bill/policy facts and optional selected document types.
- **Tests:** EN/ES text, IRS §501(r)(6) request—not guarantee—wording, legal-aid escalation, checklist choices, no writes.
- **Risks:** implying a collection freeze. Use “request,” explain routine billing may continue, and route suits/garnishment to legal aid.
- **Video:** move the in-memory tracker from applied to documents requested, build a checklist, then download the ECA-pause request. Supports **Health & Wellness** and **Community Impact**.

## F7 — Retroactive Medicaid referral (conditional)

- **Add only after F1–F6 are green:** dated official state-threshold data, parser/tests, and a result referral card.
- **Contract:** deterministic screening only; links to official state enrollment, HealthCare.gov, and Benefits.gov; no eligibility conclusion.
- **Tests:** dated state rules, unsupported-state omission, 2027 effective-date boundary, referral wording.
- **Risks:** rapidly changing rules and immigration sensitivity. Skip unverifiable states, minimize questions, and keep rules date-versioned.
- **Video:** show the referral as a possible next step, not an approval. Supports **Health & Wellness**.

## Verification and delivery

1. Baseline `pytest -q`, `npx tsc --noEmit`, and `npm run build` before feature work.
2. Red/green tests per backend module; focused front-end tests plus full commands before each commit.
3. Run backend on `:8002` and front end on `:3002`; manually exercise EN/ES, 390px, keyboard-only, and reduced motion.
4. Rebase `origin/main`, rerun everything, update `docs/CODEX_LOG.md`, push `codex/expansion`, and open a PR for Anish to merge.

