# Devpost submission text (copy and paste each field)

All numbers come from `eval/results/SUMMARY.md`. Replace `TODO_VIDEO_URL` and `TODO_DEMO_URL` before submitting.

---

## Project name
BillBack

## Tagline (≤ 60 characters)
You may not owe this bill. Find out in 60 seconds.

## Links
- Video: TODO_VIDEO_URL
- Demo: TODO_DEMO_URL (or run locally: see the README)
- Code: https://github.com/MarvinRidgeMT/BillBack

---

## Inspiration
In December 2025, 26.6% of U.S. adults said they or a family member had medical debt, and 15.4% had bills that were past due or that they couldn't pay. Of adults with medical debt, more than half owed $1,000 or more, and about 1 in 3 had been contacted by a collection agency in the past year ([Urban Institute, 2026](https://www.urban.org/research/publication/more-one-quarter-us-adults-had-medical-debt-2025)). Nonprofit hospitals have to offer free or discounted care to low-income patients, but the rules sit in long PDFs that few patients ever read. KFF Health News found hospitals sent $2.7 billion in bills over one year to patients who probably qualified for that help ([source](https://kffhealthnews.org/news/patients-eligible-for-charity-care-instead-get-big-bills/)). The nonprofit Dollar For has helped file more than 17,000 applications and get more than $60 million relieved, and its staff read each hospital policy by hand ([source](https://pmc.ncbi.nlm.nih.gov/articles/PMC12230784/)). We wanted a patient to get that answer from a photo of their bill, in about a minute.

## What it does
You take a photo of a hospital bill. BillBack reads the hospital name, address, amount due, service date and account number, and asks you to confirm anything it isn't sure about. It finds that hospital's financial assistance policy and asks two questions: household size and yearly income. Then it tells you whether you're likely to get free care, a discount, or neither, and it quotes the exact sentence and page of the hospital's own policy, with a link to the PDF. Every result says "Likely eligible, not a guarantee." One tap downloads a ready-to-sign application: a request letter to the hospital's financial assistance office (bill details, household, income, % of the poverty line, the policy quote and page, and a request to pause collections) plus a checklist of documents to attach. The whole app, the result and the PDF work in English and Spanish.

On the result screen: **"See it in the hospital's policy"** opens the real PDF page with the quoted line boxed and zoomed (if code can't find the line, it says so and draws no box); a **"What if my income were different?"** slider shows where the hospital's lines are, with every status coming from the same rules engine; **"Read it to me"** reads the result and a short phone script for the billing office aloud; a **$0 finale** when care is likely free; the **application deadline** with a days-left count and a calendar reminder made in the browser; an optional **SNAP/Medicaid/WIC** question that points to the policy's automatic-eligibility line and adds the benefit letter to the checklist; the **hospital's own application form** added to the packet when we have it (Marshfield Clinic so far; we fill in only the date); an **appeal letter** if the hospital says no; and a **state law** note for hospitals in Washington, California, Maryland, Oregon and New Jersey (information, not legal advice). The home page has a **tile map** of every hospital we've read, colored by its free-care limit: same bill, very different rules.

**How BillBack is different.** Dollar For proves this works: its advocates have filed 17,000+ applications ([source](https://pmc.ncbi.nlm.nih.gov/articles/PMC12230784/)). BillBack is the self-serve, instant version: it reads the hospital's own policy, shows the exact line, and lets a rule (not AI) decide. Undue Medical Debt buys and erases old debt after the fact ([source](https://unduemedicaldebt.org/wp-content/uploads/2026/05/Undue-Medical-Debt-2025-Impact-Report_Digital.pdf)), while BillBack tries to stop an eligible bill from becoming debt. Paid advocates like Goodbill take a share of the savings ([source](https://help.goodbill.com/en/articles/254209)); BillBack is free.

## How we built it
The backend is Python and FastAPI. Claude Sonnet 5.5 does two extraction jobs, and nothing else: reading the bill (vision) and turning each hospital policy PDF into structured rules, where every rule has a word-for-word quote, a page number and a confidence score. Code then checks the model's work: every quote has to be found in the PDF text, amounts have to parse to cents, dates have to be real, and anything under 0.8 confidence goes to the patient or to review. The eligibility decision is a plain-Python rules engine with tests, using the 2026 HHS poverty guidelines from the Federal Register. The front end is Next.js, with a confirm step for unsure fields, automatic hospital matching, and a result screen that shows the policy quote. The application PDF is built with ReportLab in memory and never saved.

## Challenges we ran into
Hospital policies contradict themselves. USA Health's policy gives two different start dates for its 240-day application window, so we added an "unclear" status that sends the field to review instead of picking one. Claude's structured output allows at most 16 nullable fields and our schema had 21, so unstated text comes back as "" and unstated page or day numbers as 0, and code turns them back into null. Our first eligibility integration quietly used 2024 poverty numbers instead of 2026; a regression test now pins the year. Several hospital links from our list pointed to an application form, a clinic fee schedule or a dead page, and we report each of those failures instead of hiding them.

We also had to be careful about what we promise:
- **Not legal or financial advice; the hospital decides.** BillBack gives a sourced "likely" result and a draft letter. The patient reviews it and sends it.
- **Asking to pause collections is a request, not a guarantee.** Federal rules ([IRS §501(r)(6)](https://www.irs.gov/charities-non-profits/billing-and-collections-section-501r6)) limit "extraordinary collection actions" while an application is pending, but routine billing contact may continue. The letter *asks* for a hold.
- **Credit reports:** the federal CFPB rule removing medical debt from credit reports was vacated by a court in July 2025 and isn't in effect ([CFPB](https://www.consumerfinance.gov/ask-cfpb/do-medical-bills-affect-my-credit-and-where-do-i-find-out-whats-in-my-medical-payment-history-en-1837/)). BillBack does not promise credit removal.
- **State laws vary** and aren't applied to the result. We show a state-law box for Washington, California, Maryland, Oregon and New Jersey; the result uses the hospital's own policy only.
- **Privacy:** BillBack doesn't save your bill or answers. The bill image is sent to our AI provider to be read, processed in memory, and discarded by our server. There are no accounts and no trackers.

## Accomplishments that we're proud of
The rules engine (plain code, no AI) gave B's hand-calculated answer for all 10 test households, using the 2026 poverty guidelines. On our 10 fake test bills (clean, angled, crumpled, dim), BillBack read 50 of 50 fields correctly, in about 2.6 seconds and about one cent per bill. Every policy quote it shows was found word for word in the hospital's PDF (21 of 21). Across 10 households × 20 synthetic policies the engine is internally consistent (200 of 200), and 263 automated tests pass. The policy reader handled 17 of the 20 real hospital policies on our list, including free-care limits of 250% and 300% and dollar income tables; 22 hospitals are in the app.

## What we learned
Getting the model to extract was the easy part; proving it extracted correctly took most of the work. Asking for a word-for-word quote plus a page number, then checking it in code, catches made-up answers cheaply. "The policy doesn't say" and "the policy is unclear" have to be different answers, or every hospital looks uncertain. And we couldn't measure everything: nobody hand-labeled real policies field by field, so we report two hand spot-checks (11 of 12 fields right) instead of claiming a bigger accuracy number. A six-policy answer key we built turned out to be AI-written, so we report its 35/36 agreement only as a cross-check, not as accuracy. A full 20-policy benchmark (120 fields) is next: 17 of 20 policies are already read, and the answer key needs independent verification by a person; the verification pack is ready. A new hospital costs about $0.053 to read the first time, just over our $0.05 target.

## What's next
Next, BillBack grows from 22 hospitals to every U.S. nonprofit hospital. Hospitals' own IRS tax filings (Form 990 [Schedule H](https://www.irs.gov/instructions/i990sh)) list the income limits each one uses, and [CMS's hospital list](https://data.cms.gov/provider-data/dataset/xubh-q36u) lets us match any bill to the right hospital. We'll check each saved policy against both, plus state charity-care laws (we already show Washington, California, Maryland, Oregon and New Jersey; New York, Illinois and Colorado come next, once we've confirmed them against the official text). After that: help for insured patients (26% of adults *with* health insurance had medical debt, per the [Urban Institute](https://www.urban.org/research/publication/more-one-quarter-us-adults-had-medical-debt-2025)), comparing the bill to the insurance statement and requesting an itemized bill; adding more hospitals' own application forms to the packet, and a higher-quality on-device English voice; and pilots with community health centers, 211 and legal aid. It stays free for patients and never sells data.

## Built with
python, fastapi, anthropic, claude, pydantic, pdfplumber, pypdf, rapidfuzz, pillow, reportlab, pytest, next.js, react, typescript, tailwindcss, web-speech-api

## Sponsor tools
None.

---

## Built during the event (required statement)
All application code in this repository was written during EvoHacks II. The commit history is the proof: the first commit is `ffe1677` (2026-11-22 00:11:53 ET), the demo build is tagged `demo-freeze`, and the submitted version is tagged `v1.0-submission`.

Pre-existing things we used:
- Python libraries from `requirements.txt`: FastAPI, Uvicorn, python-multipart, Anthropic SDK, Google GenAI SDK (optional provider), pdfplumber, pytesseract, pdf2image, httpx, pydantic, RapidFuzz, python-dotenv, pytest, ReportLab, Pillow, pillow-heif, pypdf.
- Front-end libraries from `frontend/package.json`: Next.js, React, Tailwind CSS, Motion, Lucide icons, Base UI, shadcn, class-variance-authority, tw-animate-css; fonts Anton and DM Sans (Google Fonts).
- APIs: Anthropic Claude API (Claude Sonnet 5.5); the browser's Web Speech API for "Read it to me" (no voice files bundled).
- Data: 2026 HHS poverty guidelines (Federal Register 2026-00755); 22 public hospital financial assistance policies (links in the README); Marshfield Clinic's public application form; state charity-care laws from official sources (WA RCW 70.170.060, CA Hospital Fair Pricing Act via HCAI, MD Health-General §19-214.1, OR ORS 442.614, NJ N.J.A.C. 10:52).
- Tools: we used Claude Code, an AI coding assistant, while building. Our prompts are in `docs/process/`.

## Team
- Anish Meruva (@AniMeruva-cmyk): AI and backend (policy reader, bill reader, poverty-line math, integration, evals)
- @abhinavmedisetty: eligibility rules engine, policies, answer key, households
- Siddharth Tumati (@SiddharthTumati): front end, sample bills, design, video

---

## How we meet the judging criteria
| Criterion | Where to look |
|---|---|
| Fit to the prompt | A tool that helps people facing medical bills claim help the law already gives them |
| Problem and impact | 26.6% of U.S. adults had family medical debt in 2025 (Urban Institute); $2.7B billed to likely-eligible patients in one year (KFF); Dollar For's 17,000+ applications done by hand (Health Affairs) |
| Technical execution | Two AI readers with code checks, a tested rules engine, 263 passing tests, evals in `eval/results/SUMMARY.md` |
| Usability and accessibility | Photo in, answer out in seconds; two questions; confirm step for unsure fields; English and Spanish; plain-language result |
| Appropriate use of tech | AI only extracts; plain code decides; every rule cites quote + page; low confidence goes to a person; honest limits in the README |
| Video | TODO_VIDEO_URL: a crumpled, dim bill → confirm step → "Likely free care" with the policy quote → application PDF, in English and Spanish |
