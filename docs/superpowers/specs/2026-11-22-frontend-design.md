# BillBack front end — design

Owner: Sid (Person C) · Written 2026-11-22, 2am ET · Status: approved by Sid for building

## 1. Intent and why

BillBack turns a photo of a hospital bill into a likely charity-care result and, later, a filled-in application. The front end is what patients use and what judges watch in a sub-3-minute video. It has two jobs:

1. **Be calm and clear for a stressed person** holding a bill they can't pay. Two questions, large type, nothing confusing, works on a phone, keyboard and screen reader.
2. **Be eye-catching in the first second** for the demo video and the judges. One big object in the middle of the hero, a bold palette that blends and pops, motion that is smooth in the right places and still everywhere else.

Sid's words on the feel: *"smooth in the right places, the colors feel purposeful and elegant, and it glides smoothly and effortlessly."* Plus *"eye catching, like a big object in the middle that immediately catches eyes."*

## 2. Goals, non-goals, anti-goals

**Goals**
- A hero screen that matches the approved demo (`docs/design/hero-demo.html`): a floating hospital bill in a mint sky, stamped **$0 OWED**.
- One flow that works every time: upload → read fields → confirm → two questions → result.
- Wired to the real backend: `POST /api/bill/read` and `POST /api/eligibility`.
- Every low-confidence field (under 0.8) is shown to the patient to confirm, never used silently.
- Every result says **"Likely eligible, not a guarantee"** and shows the exact policy quote it relied on.
- Strings live in `messages/en.json` and `messages/es.json` from day one, so Spanish is a translation job later, not a refactor.

**Non-goals (this build)**
- The application packet PDF (Sid builds it in a later step). The "Get my application" button is a placeholder.
- Real Spanish translations (stub `es.json` with the same keys; the toggle can be wired but translation comes later).
- Live mode (pasting a policy URL), login, saving anything, deploy.

**Anti-goals (failure even if it "works")**
- Motion everywhere, or motion that delays the patient. Motion happens at the hero, the reading moment and the result. Steps in between are calm.
- Coral or red used for bad news or warnings in a way that reads as "past due". Coral is the pop color for actions and the $0 stamp.
- Any wording that sounds like legal or financial advice, or a guarantee.
- Storing the bill or any personal data (no localStorage of fields, no analytics on fields).
- A fake result shown as if it were real. If the backend can't answer, the screen says so.

## 3. Constraints

- **Stack (chosen):** Next.js (App Router, TypeScript) + Tailwind CSS + shadcn/ui, with Motion (`motion` package, `motion/react`) for animation. Kokonut UI components (`npx shadcn@latest add @kokonutui/<name>`) are allowed where they fit, restyled to our tokens.
- **Lives in** `frontend/` at the repo root. Do not edit anything under `backend/`, `data/`, `cache/` (Anish's and B's code). Requests for backend changes go in `NOTES_FOR_TEAM.md`.
- **Backend calls go through a Next.js rewrite**, not straight to port 8000: `next.config.ts` rewrites `/api/:path*` → `${BACKEND_URL}/api/:path*`. The FastAPI app has no CORS middleware, and the rewrite avoids needing one. `BACKEND_URL` defaults to `http://localhost:8000`.
- **No API keys in the front end.** The front end holds no secrets.
- **Accessibility:** WCAG AA contrast, all controls at least 44px, visible focus ring, labels on every input, the step heading receives focus on each step change, results announced through `aria-live="polite"`, hero decoration `aria-hidden`. `prefers-reduced-motion` turns off all movement.
- **Responsive:** works at 390px wide (iPhone) and 1440px. Below 700px the hero stacks: headline, bill, CTA.

## 4. Approaches considered

| Approach | Trade-off | Decision |
| --- | --- | --- |
| **Next.js + Tailwind + shadcn + Kokonut UI + Motion** | About 15 min of setup. Same stack as Sid's reference sites (motion.dev, Kokonut UI), and it matches the team plan ("Next.js UI, Vercel") | **Picked by Sid** |
| Plain React (Vite) + same libraries | Slightly lighter. Breaks from the plan and Anish's notes for no gain | Rejected |
| Streamlit | Fastest to stand up, but it can't do the custom palette or smooth transitions, which is the core of Sid's vision | Rejected |

## 5. Visual design (decided with Sid)

### Palette — "Fresh start" (Sid picked option 1)

| Token | Light | Dark | Use |
| --- | --- | --- | --- |
| `--sky-1` | `#CFEFE0` | `#0D2C24` | Top of the sky background |
| `--sky-2` | `#EAF8F0` | `#13392F` | Bottom of the sky background |
| `--mint` | `#BFE6D3` | `#174236` | Soft fills, chips, quote box tint |
| `--ink` (forest) | `#0E3B2E` | `#E6F6EE` | Headlines, body text, primary buttons |
| `--ink-2` | `#3D6457` | `#A9CDBE` | Supporting text |
| `--card` | `#FFFFFF` | `#0F3027` | Step cards |
| `--line` | `#D6EBE0` | `#24524A` | Borders, dividers |
| `--coral` | `#FF6B4A` | `#FF6B4A` | The pop: $0 stamp, main CTA, "please check" outline, policy highlight |
| `--on-coral` | `#3B0E04` | `#3B0E04` | Text on coral (passes AA) |
| `--coral-bg` | `#FFE3DB` | `#4A1A10` | Highlight behind the policy quote, low-confidence field fill |

Rules: **never white text on mint** (fails contrast). Coral is always a fill behind dark text or an outline, never small coral text on white. Mint and forest carry the page. Coral appears in only a few places per screen.

### Type (Claude's call, Sid saw it in the demo)
- **Anton** for headlines, the logo, the stamp and the CTA circle. Big, condensed, poster energy.
- **DM Sans** for everything people read: 17px body, never below 13px.
- Load both with `next/font/google`.

### Hero (approved in the demo)
Copy exactly what `docs/design/hero-demo.html` does. It's the reference for layout, motion and timing.
- Mint sky gradient, 6 soft white clouds drifting slowly at different speeds.
- **6 torn scraps of the bill** (white paper, jagged edges, mono text fragments: `$4,8`, `DUE`, `12.00`, `ACCT`, `$657`, `88-2`) tumbling slowly. These replaced the mossy rocks at Sid's request.
- Headline in two lines, forest: **YOU MAY NOT / OWE THIS BILL** (second line indented on desktop).
- **The bill** (built in HTML/CSS, not an image): Mercy General Hospital statement with three line items and **AMOUNT DUE $4,812.00**, slightly crumpled (crease lines plus light shading), rotated -8°, sitting right of center and overlapping the end of the headline.
- **The stamp**: coral circle outline, "$0 / OWED", rotated 14°, lower right of the bill.
- Bottom left: "FREE CARE IS THE LAW / AT NONPROFIT HOSPITALS". Bottom right: "$2.7B BILLED TO PATIENTS / WHO LIKELY QUALIFIED". Both in Anton, small.
- Bottom-right corner: coral circle CTA **CHECK MY BILL**.
- Nav: BILLBACK logo left; "How it works" and "Español" right.
- Parallax: on pointer move, clouds, scraps and the bill shift by different amounts.

### App screens
The same sky stays behind everything. Each step is one white card (max 560px wide, 22px radius, soft shadow) centered under the nav, with a 4-segment progress bar at the top. Headings use Anton at 32–44px, body DM Sans.

## 6. Motion (the "right places")

Use Motion springs. Reference values from the demo: snappy spring ≈ stiffness 180 / damping 12; soft spring ≈ stiffness 120 / damping 16.

| Moment | Motion |
| --- | --- |
| Hero load | Headline lines rise 40px and fade in (staggered 120ms). The bill drifts in from up-right, rotating from 18° to settled (soft spring). After 250ms the stamp slams in from 2.4× scale and 30° to rest (snappy spring), the bill dips 6px on impact, and a coral strike-through draws across $4,812.00. The CTA pops in from scale 0. Then the bill bobs ±14px every 3.2s, forever |
| Ambient | Clouds drift ±8vw over 40–70s. Scraps tumble ±15° and ±30px over 23–35s. Parallax on pointer move |
| CTA click → app | Headline lifts 60px and fades. The bill dives down and shrinks to 0.35 while fading (650ms). The first card glides up from 60px with the soft spring |
| Step change | The old card fades up 14px (220ms). The new card glides up from 22px (soft spring). Focus moves to the new heading. Use `AnimatePresence mode="wait"` |
| Reading the bill | While waiting for the API: a pulsing coral dot and a status line ("Looking for the details that matter…"). When the response lands, each of the 5 fields slides in from the left, 420ms apart. Then the status reads "Done in X.X seconds" (from `data.seconds`) |
| Household stepper | The number pops (scale 1.4 → 1, snappy spring) on change |
| Result | A mini version of the bill sits beside the verdict. Its stamp slams in (snappy spring). Then a coral highlight sweeps across the policy quote left to right (1.1s) |
| Reduced motion | Everything appears in its final state immediately. No drift, bob, parallax or sweep |

## 7. Screens and behavior

State lives in one client component (`app/page.tsx` → `<Flow />`), as a simple state machine: `hero → upload → reading → questions → result`. Nothing is persisted. A refresh starts over.

### 7.1 Upload
- Heading: "Add your bill". Sub: "A photo or PDF works. It stays on this page and is never stored."
- Drop zone (drag and drop plus a "Choose a file" button). Accept JPG, PNG, HEIC, PDF up to 15 MB. Reject other types or larger files inline, before uploading: "That file type won't work. Try a photo or PDF under 15 MB."
- Buttons: **Try a sample bill** (coral; loads `public/samples/sample-bill.png`, a copy of `backend/tests/fixtures/bills/bill_b_photo.png`) and **Type it in instead** (ghost; opens manual entry, 7.6).

### 7.2 Reading + confirm (one screen)
- Calls `POST /api/bill/read` (multipart field `file`).
- Response envelope: `{ success, data: { fields, fields_to_confirm, seconds, model }, error }`.
  - `fields` keys: `hospital_name`, `hospital_address`, `amount_due`, `service_date`, `account_number`.
  - Each field: `{ value: string|null, confidence: 0–1, note: string, normalized: int|string|null }`. `normalized` is cents (int) for `amount_due` and an ISO date for `service_date`. Display `amount_due` from `normalized` as `$4,812.00`, and `service_date` as "Aug 14, 2026".
- Each field is a row: label, value, and a chip "97% sure". **Any field in `fields_to_confirm` (or with confidence < 0.8)** gets a coral outline, a coral-tinted fill, the label suffix "· please check this one", and an editable input prefilled with the value.
- **Which hospital is this?** Below the fields there's a select of the cached hospitals (`lib/hospitals.ts`, see below), with the best fuzzy match to `hospital_name` preselected. The last option is "My hospital isn't listed". If no match scores well, nothing is preselected, and the patient must choose.
  - "Isn't listed" → a message: "We haven't read this hospital's policy yet. You can still ask the hospital's billing office for a financial assistance application." Plus a link to Dollar For (https://dollarfor.org). The flow stops there.
- Button: **Looks right** → questions.
- Errors: a 400 shows the backend's `detail` message in plain words. A 502 or a network failure shows "We couldn't read that bill. Try a clearer photo, or type it in instead." Both offer Try again and Type it in.

### 7.3 Questions
- Heading: "Two quick questions". Sub: "Hospitals decide using household size and yearly income."
- Household size: a stepper, 1–12, default 1, with "−"/"+" buttons (aria-labels "Fewer people"/"More people") and the number in an `<output>`.
- Yearly household income, before taxes: a numeric input with a "$" prefix, formatted with commas as you type. It's required. Empty → inline error "Enter your yearly income, or 0 if none."
- Button: **See my result**.

### 7.4 Result
- Calls `POST /api/eligibility` with `{ hospital_slug, household_size, annual_income, state }`. `state` comes from `lib/hospitals.ts`.
- Response `data`: `status`, `tier`, `evidence {quote, page, confidence, verified, status}`, `caveats: string[]`, `disclaimer`, `percent_of_fpl`, `hospital_name`, `source_url`, `engine`.

| `status` | Heading | Mini-bill stamp | Notes |
| --- | --- | --- | --- |
| `likely_free` | Likely free care | $0 / OWED | — |
| `likely_discounted` | Likely a discount | `{tier.value}% / OFF` when `tier.discount_type` is `"percent_off"` and `tier.value` is set, else "−% / OFF" | Show `tier.description` if present |
| `probably_not_eligible` | Probably not eligible here | No stamp | Kind next steps: ask about a payment plan, check the bill for errors, Dollar For link |
| `cannot_determine` | We couldn't tell from this policy | No stamp | Call the billing office and ask for a financial assistance application |

- Sub line: "Your income is about {round(percent_of_fpl)}% of the federal poverty line for {n} people."
- **Policy quote box:** "{hospital_name}'s policy, page {page}:" then the quote with the coral highlight sweep. A "Read the full policy" link to `source_url` (opens in a new tab). If `evidence.verified === false`, `evidence.status !== "stated"`, or confidence < 0.8, add: "Double-check this line with the hospital."
- Caveats as a short bullet list if any.
- Always, in small text under the buttons: **"Likely eligible, not a guarantee. The hospital makes the final decision."** (Use the backend `disclaimer` too, without repeating it twice.)
- Buttons: **Get my application** (coral; for now it shows an inline note "Your filled-in application is coming in the next version", which is the placeholder until Sid builds the packet) and **Start over** (ghost; returns to the hero and replays the intro).
- **If `/api/eligibility` returns 503** (the poverty table isn't loaded yet) or the backend is unreachable, and `NEXT_PUBLIC_DEMO_MODE=1`, show a result from `lib/mock.ts` with a clear banner at the top of the card: **"Sample result: the eligibility service isn't connected yet."** If demo mode is off, show "We can't check eligibility right now. Try again in a minute."

### 7.5 Nav
"Español" toggles `lang` between `en` and `es`, which swaps strings from the message files. Until `es.json` is translated it can hold the English strings. "How it works" scrolls or jumps to a short 3-step explainer under the hero, or for now opens a small section below the fold with: 1) Snap your bill 2) Answer two questions 3) Get your result and application. Keep it simple.

### 7.6 Manual entry
The same card as 7.2, but with empty inputs for the 5 fields plus the hospital select, all editable and none pre-checked. Used when a photo fails or the patient prefers typing.

## 8. Data files the builder creates

- `lib/hospitals.ts`: the 6 hospitals with cached policies, from `cache/policies/*.json` and `data/policies/sources.csv`:

| slug | display name | state |
| --- | --- | --- |
| `usa-health` | USA Health | AL |
| `baptist-memorial-health-care-corporation` | Baptist Memorial Health Care | MS |
| `boys-town-national-research-hospital` | Boys Town National Research Hospital | NE |
| `fort-healthcare-inc` | Fort HealthCare | WI |
| `marshfield-clinic-health-system` | Marshfield Clinic Health System | WI |
| `adena-health-system` | Adena Health System | OH |

  Matching: lowercase, strip punctuation and words like "inc", "the", "corporation", then token overlap. Preselect if ≥ 0.5. Add a note to `NOTES_FOR_TEAM.md` asking A for `GET /api/hospitals` (slug, name, state) so this list stops being hardcoded once B has 20 policies.
- `lib/mock.ts`: one bill-read response and one eligibility response per status, clearly named `MOCK_*`, used only in demo mode.
- `lib/api.ts`: `readBill(file)` and `checkEligibility(body)`, typed, unwrapping the `{success, data, error}` envelope and turning FastAPI `{detail}` errors into readable messages.
- `lib/types.ts`: the TypeScript types for the shapes above.

## 9. Folder layout

```
frontend/
  package.json
  next.config.ts          # rewrites /api/:path* → BACKEND_URL
  .env.example            # BACKEND_URL=http://localhost:8000, NEXT_PUBLIC_DEMO_MODE=1
  components.json         # shadcn config + "@kokonutui" registry
  public/samples/sample-bill.png
  app/
    layout.tsx            # fonts, <html lang>, metadata
    page.tsx              # renders <Hero/> and <Flow/>
    globals.css           # tokens from section 5, Tailwind
  components/
    hero/  Hero.tsx  Sky.tsx  Scraps.tsx  FloatingBill.tsx  Stamp.tsx
    flow/  Flow.tsx  StepCard.tsx  StepBar.tsx  UploadStep.tsx  ReadingStep.tsx
           QuestionsStep.tsx  ResultStep.tsx  ManualEntry.tsx
    ui/    (shadcn / Kokonut generated components)
  lib/     api.ts  types.ts  hospitals.ts  mock.ts  motion.ts  format.ts  i18n.ts
  messages/ en.json  es.json
```

## 10. Done means

- `cd frontend && npm run build` passes, with no TypeScript errors.
- With the backend running (`.venv/bin/uvicorn backend.app:app` on :8000) and `npm run dev`, the full flow works using the sample bill. Fields come from the real API. The result comes from the real API, or from the labeled sample if the API returns 503.
- Keyboard only: the whole flow can be completed with Tab, Enter and Space, with a visible focus ring.
- With reduced motion on (macOS: System Settings → Accessibility → Display → Reduce motion), nothing moves.
- It looks right at 390px and 1440px wide, and matches the hero in `docs/design/hero-demo.html`.
- Small commits with clear messages, all in `frontend/` (plus the one `NOTES_FOR_TEAM.md` note).

## 11. Left to the builder

- Exact component breakdown inside each file, the Tailwind setup details, and whether to use a Kokonut component or hand-build (hand-build if a Kokonut piece fights the palette).
- The fuzzy-match details, as long as the patient can always override.
- Small copy tweaks, keeping the voice calm, plain and kind, with no "!" and no "please" in system copy except "please check this one".

## 12. Calls Claude made (Sid, check these)

- Fonts: Anton + DM Sans.
- Hospital matching happens in the front end with a hardcoded list of 6, plus a request to A for an endpoint.
- Demo mode shows a labeled sample result when eligibility returns 503, because A's poverty table isn't in the repo yet.
- Household size defaults to 1, not 3 as in the demo.
- "Get my application" is a placeholder until the packet PDF exists.
