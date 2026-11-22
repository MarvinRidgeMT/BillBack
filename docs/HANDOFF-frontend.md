# Handoff: build the BillBack front end

You're working for **Sid, Person C** (front end + video) on a 3-person hackathon team. `CLAUDE.md` in this repo is written from Anish's point of view (Person A, backend). Its rules apply to you too: no real patient data, no API keys in git, "Likely eligible, not a guarantee" on every result, small commits. But **you are working for Sid, and you own only `frontend/`.**

Deadline context: Gate 3 (feature freeze, everything deployed) is **9:00am ET Sunday Nov 22**. Ship the simplest thing that matches the design. Don't gold-plate.

## What to build

Read these two files fully before writing any code:

1. `docs/superpowers/specs/2026-11-22-frontend-design.md`: the approved design. It's the source of truth for screens, copy, palette, motion, API shapes and folder layout.
2. `docs/design/hero-demo.html`: the approved prototype. Open it in a browser. The hero (layout, the floating bill, the $0 stamp, the drifting clouds and scraps, timing) and the flow's feel must match it. Port its behavior to React + Motion. Don't redesign it.

Then read the backend contract you'll call: `backend/app.py`, `backend/bill_reader/schema.py`, `backend/bill_reader/reader.py` (`to_dict`), `backend/eligibility_stub.py` (`decide`), `backend/policy_reader/schema.py` (`Evidence`, `DiscountTier`), and `NOTES_FOR_TEAM.md` (section "For C (UI)").

## Rules

- Write only inside `frontend/`, plus one note appended to `NOTES_FOR_TEAM.md` (ask A for `GET /api/hospitals`; say the front end calls the API through a Next.js rewrite, so no CORS change is needed). **Do not modify `backend/`, `data/`, `cache/`, `CLAUDE.md` or the README.**
- Stack: Next.js (App Router, TypeScript, `src/` not needed), Tailwind CSS, shadcn/ui, `motion` (`import { motion, AnimatePresence, useReducedMotion } from "motion/react"`). Kokonut UI components are optional (`npx shadcn@latest add @kokonutui/<name>`); hand-build when one fights the palette.
- Scaffold non-interactively, for example `npx create-next-app@latest frontend --ts --tailwind --eslint --app --no-src-dir --import-alias "@/*" --use-npm --yes`, then `npx shadcn@latest init` with defaults.
- Pin versions in `package.json` as installed. No other new dependencies unless they clearly earn their place.
- Commit after each working milestone with clear messages, e.g. `feat(frontend): hero with floating bill and stamp`.

## Plan (do it in this order, and commit after each)

1. **Scaffold:** Next.js app in `frontend/`, Tailwind, shadcn, `motion`, fonts (Anton + DM Sans via `next/font/google`), tokens in `globals.css`, the `/api` rewrite in `next.config.ts` and `.env.example`. Run `npm run build` to check it works.
2. **Hero:** `Sky`, `Scraps`, `FloatingBill`, `Stamp`, `Hero`, matching the demo, with reduced-motion support.
3. **Flow shell:** `Flow` state machine, `StepCard`, `StepBar`, step transitions with focus management and `aria-live`.
4. **Upload + reading/confirm:** `lib/api.ts` `readBill`, the real call, fields revealed one by one, low-confidence editing, the hospital select with fuzzy match (`lib/hospitals.ts`), errors, manual entry.
5. **Questions + result:** `checkEligibility`, every status in the design's table, the quote highlight sweep, the caveats and disclaimer, and the labeled demo fallback on 503 (`NEXT_PUBLIC_DEMO_MODE=1`).
6. **i18n scaffold:** all user-facing strings in `messages/en.json`, `es.json` with the same keys (English placeholders are fine), and the Español toggle.
7. **Check (required before saying you're done):**
   - `npm run build` passes.
   - Start the backend (`.venv/bin/uvicorn backend.app:app --reload` from the repo root, which needs `.env` with the API key that Sid sets up) and `npm run dev`. Run the whole flow with `public/samples/sample-bill.png`. Report what the real API returned.
   - Do a keyboard-only pass, a reduced-motion pass, and check 390px and 1440px widths. If you can take screenshots (e.g. Playwright), do it and compare the hero against `docs/design/hero-demo.html`.
   - List anything you couldn't do or had to guess.

## When you finish

Tell Sid in plain words: what works, what's mocked and why, how to run it (two terminals: backend + `cd frontend && npm run dev` → http://localhost:3000), and what's left. Don't push. Sid reviews and pushes.
