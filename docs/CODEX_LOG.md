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
| F2 accessibility | Accessibility | Pending axe before/after | Pending | Easy read → glossary → read aloud |
| F3 languages | Accessibility; Community | Pending key counts | Human review required | Language menu → translated notice |
| F4 Schedule H | Community; trust | Pending match/agreement/conflict counts | Omit unknown filings | Result → Schedule H badge |
| F5 navigator | Community | Pending case/zip tests | Tab memory only | Navigator toggle → cases → download all |
| F6 follow-up | Health; Community | Pending letter tests | Request, not guarantee | Result → tracker → follow-up letter |
| F7 Medicaid | Health | Conditional | Only verified states | Result → referral card |

## TODO(team)

- **A:** Expand the bill reader's structured contract with line items so the deterministic EOB matcher can compare individual services instead of conservatively requesting itemization.

## 2026-11-23 — F1 insurance mode complete

- Added an in-memory photo/PDF insurance-statement reader with a strict Pydantic schema, structured JSON, one schema retry, amount/date normalization, source locations, confidence scores, and mandatory confirmation below `0.8`. The contract deliberately excludes names, member IDs, dates of birth, and diagnoses.
- Added deterministic claim matching and seven discrepancy types. The rules compare date, provider, and amounts; show both source values; use “discrepancy” language; and never affect charity-care eligibility.
- Added EN/ES itemized-bill and billing-hold request PDFs. The billing-hold copy explicitly says it is a request, not a guarantee.
- Added the complete UI path: optional EOB picker, fictional sample-with-insurance, confirmation screen with source locations, result cross-check, call script, and both letters. All patient data remains React/request memory only.
- Added three clearly fictional PDF fixtures and browser demo files: clean, discrepancy, and denial.
- Verification: `20 passed` focused backend tests; `283 passed, 2 skipped` full backend suite; `npx tsc --noEmit`, `npm run lint`, and `npm run build` pass.
- Research wording correction: the cited 2025 Urban Institute result is **26.6% of adults ages 18–64 in families with medical debt**, not 26% of insured adults. We do not show the inaccurate claim. Source opened: <https://www.urban.org/research/publication/more-one-quarter-us-adults-had-medical-debt-2025>.
- Video: **Check my bill → Try a sample with insurance → confirm the bill → review the fictional EOB → answer questions → show the side-by-side $4,812/$620 discrepancy → open both letter buttons.**
