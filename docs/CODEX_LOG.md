# Codex expansion log

## 2026-11-23 — setup and plan

- Created isolated worktree `~/BillBack-codex` on `codex/expansion` from `main` at `f73d9cb`.
- Copied `.env` locally; it remains ignored and will never be committed.
- Read repository guidance, architecture, expansion research, backend reader/eligibility/packet contracts, and the current flow/result/accessibility code.
- Wrote `docs/CODEX_PLAN.md` with feature contracts, tests, risks, and video paths.
- The requested accessibility skills were not installed in this Codex session, so the implementation will follow their intent using Playwright/axe and manual keyboard/zoom/reduced-motion checks.

## Evidence ledger

| Feature | Award | Evidence | Limits / TODO(team) | Video path |
|---|---|---|---|---|
| F1 EOB reconciliation | Multimodal; Health | 3 fictional EOB PDFs; 20 focused tests; 283 backend tests pass; production UI build passes | The bill reader currently extracts totals rather than line items, so itemization is conservatively flagged. | Upload → add insurance statement → confirm → discrepancies → letters |
| F2 accessibility | Accessibility | 26 final axe state/locale/viewport scans: 0 violations at any severity; 1 serious stamp contrast rule fixed; 44px minimum small actions | Manual screen-reader user testing remains | Easy read → glossary → read aloud |
| F3 languages | Accessibility; Community | 5-locale menu; 298 complete EN/ES keys; 107 critical-flow keys in each new locale; 4 i18n tests | VI/ZH-CN/TL are AI-translated previews with English fallback and need human review | Language menu → translated notice |
| F4 Schedule H | Community; trust | 22 cached hospitals checked; 3 conservative matches with comparable data; 2 agree; 1 conflict | 19 unknown/unmatched filings omitted; ProPublica rendered-XML fallback used for Deflate64 archives | Result → Schedule H badge |
| F5 navigator | Community | 1 browser journey covers third-person flow, case state, printable summary, packet ZIP, and status update | Anonymous case labels; tab memory only; EN/ES packet generation | Navigator toggle → cases → download all |
| F6 follow-up | Health; Community | 6 backend letter/API tests + browser checklist download | Collections pause is a request; urgent legal notices route to legal aid | Result → tracker → follow-up letter |
| F7 Medicaid | Health | Ohio-only 138% adult-group referral with 2026 state/CMS sources; browser journey covers display/link | Referral, not decision; 49 states omitted pending current official verification | Ohio result at ≤138% FPL → referral card |

## TODO(team)

- **A:** Expand the bill reader's structured contract with line items so the deterministic EOB matcher can compare individual services instead of conservatively requesting itemization.
- **C:** Run a manual VoiceOver/Safari and NVDA/Chrome pass with disabled users before the final video; automated axe is necessary but not sufficient.
- **C:** Arrange native-speaker review for Vietnamese, Simplified Chinese, and Tagalog. Each preview currently has 107 translated critical-flow keys; less-used result extras fall back to English until reviewed.
- **B:** Review the 19 cached hospitals without a conservative Schedule H match. Add an EIN only after confirming the legal entity and hospital facilities; never infer one from a similar name.
- **B:** Verify current adult Medicaid thresholds, application links, and any state retroactive-coverage waivers before expanding the referral beyond Ohio. Unverified states are intentionally omitted.

## 2026-11-23 — F4 IRS Schedule H cross-check complete

- Added a reproducible public-data script that searches ProPublica conservatively, finds each matched EIN in the current IRS e-file index, locates the latest Form 990, and parses Schedule H FPG fields across XML schema variants.
- Current IRS ZIP batches use Deflate64. When the standard XML reader cannot decode that member, the script uses ProPublica's rendering of the same IRS XML; the rendered element IDs retain the exact XML path. Every committed record identifies that fallback explicitly.
- Checked all **22** cached hospitals. **3** had a high-confidence legal-name/state match, a latest filing, unambiguous Schedule H values, and a comparable current policy: **2 agree** (Adena, Texas Health Resources) and **1 conflicts** (Banner reports discounted care at 200% in its 2024 tax-period filing, while the cached current policy says 400%). The other 19 get no badge; nothing is guessed.
- Added a result badge with the tax period, filing link, older-filing warning, and explicit statement that this public-data cross-check never changes the eligibility result.
- Sources opened: IRS Form 990 downloads <https://www.irs.gov/charities-non-profits/form-990-series-downloads>, current Schedule H instructions <https://www.irs.gov/instructions/i990sh>, IRS XML schemas <https://www.irs.gov/e-file-providers/current-valid-xml-schemas-and-business-rules-for-exempt-organizations-and-other-tax-exempt-entities-modernized-e-file>, and ProPublica's nonprofit API <https://projects.propublica.org/nonprofits/api/>.
- Verification: 5 focused parser/data tests pass; TypeScript and 4 catalog tests pass. Full-suite/build results are recorded at the final integration pass.
- Video: **use the fictional sample (mapped to Adena) → result → show “IRS filing cross-check” with 200% agreement, tax period, source link, and the “does not change your result” line.**

## 2026-11-23 — F5 navigator mode complete

- Added the “I'm helping someone else” header toggle, third-person upload/questions/result wording, and an explicit notice that cases live only in the current tab and vanish when it closes.
- Added anonymous in-memory cases with `started`, `result ready`, and `packet downloaded` states. No account, browser storage, analytics, or server-side case storage is used.
- Added an EN/ES printable one-page take-home summary for every completed case.
- Added “Download everything,” which builds one client-side ZIP containing each case's generated application PDF, take-home HTML summary, and `.ics` reminder when the policy provides a computable deadline. A failed case packet does not get silently marked downloaded.
- Added `fflate` 0.8.3 pinned exactly. The npm registry reports its license as MIT; it is not GPL.
- Verification: the Playwright navigator journey exercises the third-person entry, one complete case, status transition, summary action, generated ZIP download, and downloaded state. TypeScript, lint, and localization catalog tests pass.
- Video: **turn on “I'm helping someone else” → Try a sample with insurance → complete the result → show Case 1 and its status → Print one-page summary → Download everything → show “Packet downloaded.”**

## 2026-11-23 — F6 follow-up kit complete

- Added an in-memory four-step tracker: applied → documents sent → decision → appeal. Refreshing or closing the tab clears it.
- Added EN/ES status-request letters for “I haven't heard back,” plus an EN/ES checklist builder for six common document categories. The checklist tells patients to send only what the hospital's policy requires, use copies, and keep originals.
- Added an EN/ES request to pause extraordinary collection actions while a complete, timely financial-assistance application is being decided. Every surface says this is a request, not a guarantee. It directs court papers, lawsuits, bank levies, and wage-garnishment notices to local legal aid/a lawyer immediately and warns not to miss court deadlines.
- Current IRS basis verified on Nov. 23, 2026: §501(r)(6) requires reasonable efforts before extraordinary collection actions; after a complete application during the application period, the hospital must timely suspend ECAs, decide eligibility, and notify the person in writing. Source opened: <https://www.irs.gov/charities-non-profits/billing-and-collections-section-501r6>.
- All PDFs are generated and streamed in memory with `Cache-Control: no-store`; none are written to disk.
- Verification: **6** focused backend letter/API tests pass in both languages; the browser journey selects a document and downloads the checklist; full backend is **294 passed, 2 skipped**; TypeScript, lint, catalog tests, and production build pass.
- Video: **result → What happens after you apply → click Applied and download the status request → click Documents sent and select proof of income → download the checklist → show “I got a collections notice” and its legal-aid warning/request letter.**

## 2026-11-23 — F7 retroactive Medicaid referral complete (verified Ohio scope)

- Added a referral when an Ohio household is at or below 138% FPL. It explicitly says other rules apply, only the state decides, and this is not a BillBack eligibility determination.
- The card links to Ohio's official application instructions, HealthCare.gov, and the current USA.gov Benefit Finder (the former Benefits.gov now redirects there).
- Current rule copy says Medicaid may cover eligible care from up to three months before the application month and tells the person to ask the state about this bill. It also warns that for applications on or after Jan. 1, 2027, Public Law 119-21 §71112 limits the federal window to one month for expansion adults and two months for other Medicaid groups.
- Official sources opened Nov. 23, 2026: Ohio's Group VIII page (138% FPL) <https://medicaid.ohio.gov/families-and-individuals/citizen-programs-and-initiatives/medicaid-group-viii>, Ohio application instructions <https://medicaid.ohio.gov/families-and-individuals/coverage/01-how-to-apply>, and CMS's Nov. 18, 2025 enrollment bulletin <https://www.medicaid.gov/federal-policy-guidance/downloads/cib11182025.pdf>.
- Scope is deliberately Ohio-only. The other 49 states show no referral until a current official threshold/application link and any retroactive-coverage waiver are checked.
- Verification: the browser journey uses an Ohio fixture at 130% FPL, confirms the referral appears, and verifies the application link points to Ohio Medicaid.
- Video: **use the Adena/Ohio sample with income at or below 138% FPL → result → show “You might also qualify for Medicaid” → point out “referral, not a decision,” the retroactive-coverage note, 2027 change, and official Ohio application link.**

## 2026-11-23 — final integration

- Rebasing check against `origin/main` completed; the branch was already current with no conflicts.
- Final backend: **294 passed, 2 skipped**.
- Final frontend: **4 localization tests**, **1 complete navigator/follow-up/Medicaid browser journey**, TypeScript, ESLint, and the production Next.js build all pass.
- Final accessibility: **4 Playwright tests** covering **26 state/locale/viewport scans** pass with **0 axe violations at any severity**, including English/Spanish, desktop/390px, keyboard focus, reduced motion, and 200% easy-read zoom.
- Dependency review: `fflate` 0.8.3 is MIT; Playwright is Apache-2.0; axe-core Playwright is MPL-2.0. No GPL dependency was added.
- No real patient data, secrets, analytics, accounts, or user-data persistence were added. Generated PDFs and ZIPs remain in request/browser memory.

## 2026-11-23 — F2 accessibility pack complete

- Added an in-memory easy-read mode with about 20px base text, more space, and one-column fact rows that hold at 200% zoom and 390px.
- Added a human-written EN/ES glossary for six billing/policy terms. Each definition is keyboard and screen-reader accessible through native disclosure controls.
- Extended device-local read-aloud to the bill confirmation and questions; the active sentence is visually highlighted and nothing autoplays or leaves the device.
- Raised small action targets to 44px and preserved the existing 48px primary controls and visible focus rings.
- Added Playwright + axe coverage for six patient states × two languages × two viewports, plus easy-read/keyboard/zoom checks. Before: one serious contrast rule on the result stamp (two nodes, 2.81:1). After: **0 serious or critical findings across 26 final scans**. See `docs/ACCESSIBILITY.md`.
- Dependency license check: Playwright is Apache-2.0; axe-core Playwright is MPL-2.0; neither is GPL.
- Video: **open Check my bill → turn on Easy read in the header → open a glossary definition → use Read it to me on confirmation/questions → resize to the 390px phone view.**

## 2026-11-23 — F3 responsible language previews complete

- Replaced the EN/ES toggle with a keyboard-accessible five-language menu: English, Spanish, Vietnamese, Simplified Chinese, and Tagalog.
- Added 107 AI-translated critical-flow strings per new locale, including upload, confirmation, insurance, questions, core result, and glossary copy. Untranslated lower-frequency extras visibly fall back to English instead of pretending to be reviewed translation.
- Every new locale shows a persistent warning that the translation was made by AI, advises asking the hospital for its official version, and explains that generated letters/PDFs remain EN/ES. The code routes non-Spanish packet requests to English safely.
- Census basis: the 2019 ACS language report identifies Chinese, Tagalog, and Vietnamese among the five most common non-English languages and reports substantial limited-English rates, especially Chinese and Vietnamese. Primary source opened: <https://www.census.gov/library/publications/2022/acs/acs-50.html>.
- IRS wording: hospitals must translate FAP documents for each LEP language group meeting the lesser of 1,000 people or 5% of the community served/likely encountered, and make translations available as the English version is. Primary source opened: <https://www.irs.gov/charities-non-profits/financial-assistance-policy-and-emergency-medical-care-policy-section-501r4>.
- Verification: 4 catalog tests pass; EN/ES have identical 298-key catalogs; all three previews contain the disclosure and required patient-flow keys; TypeScript, lint, production build, and the 26 accessibility scans pass.
- Video: **open the header language menu → choose Tiếng Việt (then 简体中文 or Tagalog) → show the persistent AI-translation/official-version/EN-ES-letter notice → move into Add your bill.**

## 2026-11-23 — F1 insurance mode complete

- Added an in-memory photo/PDF insurance-statement reader with a strict Pydantic schema, structured JSON, one schema retry, amount/date normalization, source locations, confidence scores, and mandatory confirmation below `0.8`. The contract deliberately excludes names, member IDs, dates of birth, and diagnoses.
- Added deterministic claim matching and seven discrepancy types. The rules compare date, provider, and amounts; show both source values; use “discrepancy” language; and never affect charity-care eligibility.
- Added EN/ES itemized-bill and billing-hold request PDFs. The billing-hold copy explicitly says it is a request, not a guarantee.
- Added the complete UI path: optional EOB picker, fictional sample-with-insurance, confirmation screen with source locations, result cross-check, call script, and both letters. All patient data remains React/request memory only.
- Added three clearly fictional PDF fixtures and browser demo files: clean, discrepancy, and denial.
- Verification: `20 passed` focused backend tests; `283 passed, 2 skipped` full backend suite; `npx tsc --noEmit`, `npm run lint`, and `npm run build` pass.
- Research wording correction: the cited 2025 Urban Institute result is **26.6% of adults ages 18–64 in families with medical debt**, not 26% of insured adults. We do not show the inaccurate claim. Source opened: <https://www.urban.org/research/publication/more-one-quarter-us-adults-had-medical-debt-2025>.
- Video: **Check my bill → Try a sample with insurance → confirm the bill → review the fictional EOB → answer questions → show the side-by-side $4,812/$620 discrepancy → open both letter buttons.**
