# BillBack accessibility audit

Audit date: 2026-11-23
Tooling: Playwright 1.57.0 + axe-core 4.10.2, Google Chrome, automated fixtures only
Scope: hero, upload, bill confirmation, insurance confirmation, questions, and result in English and Spanish; desktop and 390×844 phone viewports; reduced-motion preference; easy-read mode at 200% zoom; keyboard focus.

## Results

| Measurement | Before | After |
|---|---:|---:|
| Serious axe rules on the complete English result screen | 1 | 0 |
| Critical axe rules | 0 | 0 |
| Serious/critical rules across the final 26 state/locale/viewport scans | — | 0 |

The before scan found `color-contrast` on the decorative result stamp: coral text on white measured 2.81:1 in two nodes. The stamp text now uses the dark ink color while preserving the coral border. A later heading-order cleanup removed the remaining moderate findings. The final suite reports **zero axe violations of any severity across all 26 scans** in either locale or viewport.

Run `npm run test:a11y` from `frontend/` to reproduce the state-by-state output.

## Product changes reviewed

- Easy-read mode stays in React memory only. It uses roughly 20px body text, increased line spacing, single-column fact rows, and a wider card that still fits the viewport.
- A human-written EN/ES glossary explains deductible, coinsurance, federal poverty level, presumptive eligibility, amounts generally billed, and collections in short sentences.
- The existing device-local read-aloud control now reads bill confirmation and the two questions, with the active sentence highlighted.
- Small action controls have a minimum 44px target; the standard button component remains 48px tall.
- Visible keyboard focus, heading focus on step changes, reduced-motion behavior, 390px layout, and 200% zoom are exercised by the Playwright suite.

## Limits

- Automated checks do not replace testing with disabled people or with VoiceOver, NVDA, and TalkBack.
- Device voices vary. Read-aloud never starts automatically, and the same words always remain visible.
- **TODO(team C):** conduct a short VoiceOver/Safari and NVDA/Chrome manual pass before the final video.
