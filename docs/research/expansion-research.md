> Desk research by the team (AI-assisted, Nov 22, 2026). Claims marked unverified in the text weren't independently checked. The HospitalAid open-data figures (3,496 hospitals) also couldn't be independently confirmed, so the submission doesn't cite them.

# BillBack Expansion Research — Complete Package

**Prepared:** November 22, 2026  
**Purpose:** Consolidated research deliverable for EvoHacks II  
**Scope:** Research only; no application code or team repository files were changed.

## Contents

1. [Devpost “What’s next?”](#billback--devpost-whats-next)
2. [Full expansion report](#expanding-billback-national-research-report)
3. [Prioritized roadmap](#billback-expansion-roadmap)
4. [Schedule H feasibility note](#schedule-h-as-a-national-policy-discovery-backbone)

---

# BillBack — Devpost “What’s next?”

## Ready-to-paste paragraph (5 sentences)

Next, BillBack will expand from a focused prototype into a nationwide, evidence-linked navigator that matches a hospital bill to the correct facility, current financial-assistance policy, IRS Schedule H filing, and applicable state protections. We will add an insured-patient workflow that compares the bill with the explanation of benefits, identifies discrepancies for human review, and prepares itemized-bill, correction, appeal, and financial-assistance requests without promising that any charge is wrong. A follow-up layer will track application deadlines, documentation requests, and written collection-hold requests, while routing people to retroactive Medicaid screening, legal aid, or a trained navigator when automation is unsafe. We will pilot through community health centers, 211 networks, libraries, credit unions, unions, and benefits teams, measuring verified dollars forgiven or refunded, approvals, time to resolution, collections avoided, and equity by language and geography. BillBack will remain free to patients while pursuing grants and carefully governed institutional distribution partnerships that cannot influence eligibility results or sell user data.

## Five verified statistics for the pitch video

1. **26.6% of U.S. adults** reported that they or someone in their family had medical debt in December 2025; **15.4%** had debt that was past due or could not be paid. Source: Urban Institute, *More than One-Quarter of U.S. Adults Had Medical Debt in 2025*, October 6, 2026; accessed November 22, 2026. <https://www.urban.org/research/publication/more-one-quarter-us-adults-had-medical-debt-2025>
2. Among adults with medical debt in that survey, **53.8% owed at least $1,000**, **15.5% owed at least $5,000**, and **35.2%** said a collection agency contacted them in the prior year. Source: Urban Institute, October 6, 2026; accessed November 22, 2026. <https://www.urban.org/research/publication/more-one-quarter-us-adults-had-medical-debt-2025>
3. **72.9% of adults with past-due medical debt said they owed at least some of it to hospitals**, and **63.5%** of adults with past-due hospital debt incurred all of it while insured, in a nationally representative June 2022 survey. Source: Urban Institute, *Most Adults with Past-Due Medical Debt Owe Money to Hospitals*, March 2023; accessed November 22, 2026. <https://www.urban.org/sites/default/files/2023-03/Most%20Adults%20with%20Past-Due%20Medical%20Debt%20Owe%20Money%20to%20Hospitals_0.pdf>
4. Nonprofit hospitals reported **$2.7 billion in bad debt attributable to patients who were probably eligible for financial assistance** in the reporting year examined; the estimate covered 1,134 nonprofit organizations operating 1,651 hospitals and was likely incomplete because it depended on hospital self-reporting. Source: KFF Health News, *Patients Eligible for Charity Care Instead Get Big Bills*, December 2019; accessed November 22, 2026. <https://kffhealthnews.org/news/patients-eligible-for-charity-care-instead-get-big-bills/>
5. Dollar For’s policy dataset contained income eligibility data for **2,770 hospitals—92% of U.S. private nonprofit hospitals—by March 14, 2024**; its intervention had supported more than 17,000 applications and facilitated more than **$60 million** in relief since 2019. Source: *Health Affairs Scholar*, *US Nonprofit Hospitals’ Financial Assistance Policies, 2024*, November 2024 (PubMed Central version posted 2025); accessed November 22, 2026. <https://pmc.ncbi.nlm.nih.gov/articles/PMC12230784/>

**Accuracy note:** The KFF survey statistic sometimes summarized as a “billing error rate” actually measures whether respondents *thought* they had received an erroneous bill; it is not an audited error rate. BillBack should not use “80% of medical bills contain errors,” for which this research found no reliable national primary source. See KFF, July 14, 2022; accessed November 22, 2026: <https://www.kff.org/private-insurance/could-consumer-assistance-be-helpful-to-people-facing-medical-debt/>.

## How BillBack differs (3 sentences)

Dollar For provides high-touch financial-assistance application support using a manually reviewed policy database, while BillBack’s wedge is an immediate, source-linked bill-to-policy assessment and editable document package that a patient controls. Undue Medical Debt primarily erases debt later by acquiring donated or purchased portfolios, while BillBack tries to prevent eligible hospital balances from becoming debt in the first place; Goodbill and paid advocates such as Resolve focus more on bill auditing or negotiated reductions, often with fees tied to savings. New AI advocates can draft disputes, but BillBack differentiates through transparent eligibility logic, facility-level policy provenance, state-law floors, privacy minimization, and explicit handoffs when a machine should not decide.

Competitor references: Dollar For evidence in *Health Affairs Scholar*, November 2024, <https://pmc.ncbi.nlm.nih.gov/articles/PMC12230784/>; Undue Medical Debt, 2025 Impact Report published May 2026, <https://unduemedicaldebt.org/wp-content/uploads/2026/05/Undue-Medical-Debt-2025-Impact-Report_Digital.pdf>; Goodbill FAQ and pricing, edited October 4, 2023 and accessed November 22, 2026, <https://www.goodbill.com/faq> and <https://help.goodbill.com/en/articles/254209>; Resolve, undated current service page accessed November 22, 2026, <https://www.resolvemedicalbills.com/lp/medical-bill-advocate>.

## Responsible-use caveats

- BillBack provides sourced information and editable drafts, not legal advice, representation, a guaranteed eligibility decision, or a promise that a bill is wrong; the hospital, insurer, agency, or court makes the final decision, and high-stakes cases should be routed to qualified help.
- A request does not automatically stop every collection action or remove accurate credit information. The product must distinguish a request for a hold from a legally required suspension, track changing federal and state rules, and never promise credit deletion.
- Bills, explanations of benefits, tax documents, and applications can contain sensitive health and financial information. Collect only fields needed for the task, avoid advertising trackers and secondary use, encrypt data, give users deletion/export controls, and do not claim HIPAA compliance or “nothing is stored” unless the architecture and contracts actually support the claim.

---

# Expanding BillBack: national research report

**Prepared:** November 22, 2026  
**Scope:** desk research for EvoHacks II; no legal advice and no application code  
**Method:** primary statutes, regulations, agency data, peer-reviewed research, and current official product pages were preferred. “Current” means verified as of the access date. Where a market actor’s scale or pricing could not be independently confirmed, it is marked unverified.

## Executive conclusion

BillBack can scale nationally, but the durable product is an **evidence pipeline**, not a one-time library of PDFs. CMS data should define the hospital universe; IRS Schedule H should discover and cross-check nonprofit facility rules; live financial-assistance policies (FAPs), applications, summaries, and covered-provider lists should supply operational detail; state law should remain a separate, date-versioned rights layer; and every patient-facing value should retain page-level provenance. The most useful near-term expansion is not generalized bill negotiation. It is (1) verified national policy coverage with state-law overlays, (2) an insured-patient bill/EOB reconciliation and itemized-bill workflow, and (3) deadline-aware follow-up, appeals, and public-benefit screening.

# 1. Scaling the policy data (most important)

## 1.1 What Schedule H reports—and what it does not

The IRS’s 2025 Schedule H instructions say Part I, line 3a reports the FPG percentage at or below which the filing organization provides free care under the policy serving the largest number of patients; line 3b reports the discounted-care threshold; and line 3c flags asset or other eligibility tests. Part V, Section B, line 13 repeats criterion types and specific free/discount FPG thresholds for each hospital facility, while lines 14–20 cover amounts-generally-billed (AGB) methodology, applications, publicity, extraordinary collection actions (ECAs), and reasonable efforts. A filer can enter “000” when it does not use FPG percentages and explain other tests in Part VI.[S1]

That is enough to answer “does the latest filing broadly agree with the extracted policy threshold?” It is not enough to reconstruct a policy. The return may omit intermediate discount tiers, provider exclusions, document rules, presumptive pathways, appeal procedure, current application URLs, or the exact deadline. It also describes a completed tax period and filing, not necessarily today’s policy. Confidence in those limitations is **high**, because they follow directly from the form instructions; expected automated facility-match yield remains **medium** until BillBack tests several filing/schema years.[S1]

## 1.2 Bulk access and update design

| Source | What BillBack gets | Currency/access | Proper role |
|---|---|---|---|
| IRS Form 990 XML downloads | Full e-filed returns, including Schedule H attachments and narratives | IRS posts calendar-year ZIPs and index files; its bulk page says XML is generally updated monthly.[S2][S3] | Authoritative filing content; download, parse, and version locally. |
| IRS TEOS index | Return ID, filing type, EIN, tax period, submission date, taxpayer name, DLN, and object ID | Current official index; field definitions are in the TEOS FAQ.[S3] | Incremental ingest, deduplication, amended-return detection, lineage. |
| ProPublica Nonprofit Explorer API | Organization lookup by EIN and convenient filing/PDF/XML discovery | API v2 is public; summary values are a subset of the return.[S4] | Developer convenience and fall-back discovery, not the threshold source of record. |
| CMS Hospital General Information | CCN/facility ID, name, address, phone, hospital type, ownership | Current dataset reviewed here was modified October 26 and released November 12, 2026; 5,435 rows.[S5] | Base facility universe and bill-to-facility matching. |
| CMS Provider of Services/QIES data | Medicare-certified provider demographics and certification attributes | CMS publishes a QIES POS methodology; production cadence and field availability must be monitored per release.[S6] | Identity/history cross-check, especially certification and facility changes. |
| NPPES/NPI bulk data | Type 2 organization legal/other names, practice locations, and endpoints | CMS posted a monthly file dated November 9, 2026 plus weekly incrementals.[S7] | Aliases and locations only. Public dissemination suppresses EIN/TIN, and NPI does not prove ownership or policy coverage.[S7] |
| AHA Annual Survey | System relationships and extensive hospital attributes | Licensed commercial product; AHA describes 5,000+ hospitals, 400 systems, and more than 1,300 fields.[S8] | Optional paid match enhancement; national public-interest coverage must not depend on it. |

Recommended ingest: poll the IRS index monthly; store return metadata, raw XML, schema year, source URL, and checksum; preserve amended and superseded versions; parse filing-organization and facility records separately; and generate evidence pointers back to exact XML nodes. A version adapter is necessary because IRS XML tag names change. Zero, blank, and narrative values must route to review rather than become eligibility conclusions.[S1][S2][S3]

## 1.3 Matching a bill to the correct hospital

Start with CMS’s facility-level universe and use CCN when a bill or policy exposes it. Otherwise, normalize legal and trade names, street suffixes, suite text, city, ZIP, phone, URL domain, and health-system aliases; score every candidate; and ask the patient to confirm whenever the lead is not decisive. A “hospital” name on a bill can identify a parent, campus, professional group, laboratory, or revenue-cycle vendor, so BillBack should show the matched legal facility, service location, and policy scope rather than silently choose.[S5][S6][S7]

Schedule H must preserve the parent-EIN-to-Part-V-facility relationship. An organization-level threshold is not proof that every campus uses that rule. NPPES is helpful for aliases, but CMS expressly suppresses EIN/TIN in public dissemination; an NPI therefore cannot be used as the missing EIN bridge without another source.[S1][S7]

## 1.4 Finding the live FAP

For tax-exempt hospitals, §501(r)(4) requires a current FAP, application, and plain-language summary to be widely publicized. IRS guidance requires conspicuous website links, free downloads without an account or personal information, paper availability, notice on billing statements, and translated versions when specified language-population thresholds are met. The FAP must also list covered and non-covered providers.[S9]

This makes automated discovery plausible but not trivial. Documents can live on a parent-system domain, be JavaScript-linked, use nonstandard names, be scanned PDFs, move without redirects, or leave an old PDF indexed. BillBack should crawl the official domain and sitemap for FAP/financial-assistance/charity-care/application/plain-language/provider-list terms; verify that the facility is named; extract policy and effective dates; save content hashes and rendered snapshots; and retain all competing versions until a reviewer resolves them. Link availability is evidence of publication, not evidence that the rule was parsed correctly.

## 1.5 Existing datasets and whether to build or partner

| Dataset/organization | Verified coverage or method | Use and limitation |
|---|---|---|
| HospitalAid open data | Version released November 21, 2026 says it covers 3,496 hospitals; 2,356 quote free-care thresholds, with 2,171 supported by verified policy, 979 by Schedule H, and 346 by a state program. It includes CCN, tiers, criteria, URLs/evidence, and is CC BY 4.0.[S10] | Strongest immediate open accelerator. Attribute, independently validate, and preserve BillBack’s own source lineage. |
| Dollar For research dataset | Peer-reviewed paper reports income-policy data for 2,770 hospitals, 92% of private nonprofit hospitals, as of March 14, 2024. It used manual policy review, quarterly software checks, two reviewers, consensus, and attorney input.[S11] | Best published quality benchmark. The dataset is not established here as an open/current feed; partnership or license terms are unverified. |
| State repositories | California HCAI and Washington DOH publish hospital policies/applications; Oregon publishes statewide assistance information.[S12][S13][S14] | High-value authoritative seeds in covered states; formats and scope vary. |
| Lown Institute | Its 2026 fair-share analysis covers 3,037 hospitals using FY2023 IRS, CMS, and property-value data; its policy work is suited to benchmarking, not a live application-rule feed.[S15] | Useful public-accountability partner and scorecard method reference. |
| AHA | Licensed survey and daily demographic maintenance, with annual survey updates.[S8] | Optional identity enrichment; cost and redistribution restrictions require procurement review. |

**Recommendation:** build the source-of-truth and reconciliation layer, while licensing or importing permissively licensed seed data where it saves time. HospitalAid can bootstrap breadth; IRS/CMS/live FAPs should make the record reproducible; selected state repositories should improve authority; and human review should focus on conflicts, missing data, and high-volume hospitals. A public correction channel and quarterly full-policy checks should complement monthly IRS/CMS ingestion.[S10][S11]

## 1.6 Quality gates for nationwide coverage

- A record is “patient-ready” only when the facility match, current policy URL, effective/retrieval date, core thresholds, and page-level evidence are present.
- Schedule H agreement increases confidence but never substitutes for the live tier schedule. A disagreement creates a review ticket.
- State law is a separate versioned floor. If a published hospital policy appears less protective, show the conflict and legal source; do not silently alter the policy text.
- Publish coverage by facility and field, not a single “percent complete.” Audit stratified samples by ownership, state, rurality, PDF type, and schema year.
- Track false facility matches, threshold/tier extraction accuracy, stale-link rate, conflict rate, reviewer agreement, and user-reported denials. The current 83–100% hand spot-check range on six policies is promising prototype evidence, not a national accuracy estimate.

# 2. Legal and policy landscape

## 2.1 Federal §501(r) baseline for tax-exempt hospitals

| Requirement | Current rule and product implication |
|---|---|
| Written FAP and emergency policy | A §501(c)(3) hospital facility must establish a written FAP describing eligibility, basis for amounts charged, application method, collection actions, and widely publicize it; it also needs an emergency-medical-care policy. Include the application, plain-language summary, translations, and provider list in the document set.[S9][S16] |
| AGB cap | A FAP-eligible person cannot be charged more for emergency or medically necessary care than amounts generally billed to insured patients. Hospitals may use a look-back or permitted prospective method; other care must be below gross charges.[S17] |
| Notification and application periods | IRS guidance describes a 120-day notification period from the first post-discharge billing statement before ECAs and a 240-day application period; a required 30-day ECA notice can extend the practical deadline. Incomplete and complete applications trigger specified notice, assistance, determination, refund/reversal, and suspension duties.[S18] |
| ECAs | Examples include some debt sales, adverse credit reporting, liens, foreclosure, property seizure, civil action, arrest/body-attachment processes, wage garnishment, and deferring/denying or requiring prepayment for medically necessary care because of prior nonpayment.[S18] |

Important wording for BillBack: a submitted FAP application can require suspension of ECAs during processing under §501(r)(6), but that is not a promise that every routine billing contact stops. A generated letter should request a hold, identify the pending application, ask for written confirmation, and preserve delivery evidence.[S18]

## 2.2 State charity-care protections beyond the federal floor

The table is a verified comparison, not a 50-state legal opinion. “All hospitals” means the facilities described in the cited state law; professional bills may still be outside scope. Thresholds use household/family income and FPL/FPG as defined by the state rule.

| State | Law/citation | Income threshold | Coverage and key rights | Confidence/currentness |
|---|---|---|---|---|
| Washington | RCW 70.170.060[S19] | Tier 1 systems: free ≤300% FPL, 75% discount at 301–350%, 50% at 351–400%. Tier 2: free ≤200%, 75% at 201–250%, 50% at 251–300%. | Applies to hospital care and includes insured patient responsibility; notice, translations, and eligibility assistance are required elsewhere in chapter. | High; current statute accessed Nov. 22, 2026. |
| California | Hospital Fair Pricing Act, Health & Safety Code §§127400–127446; HCAI FAQ[S20] | Self-pay patients and patients with high medical costs at ≤400% FPL qualify for charity or discounted care; “high medical costs” includes 12-month out-of-pocket medical expenses above 10% of family income. | Acute-care hospitals; expected payment is capped by Medicare/Medi-Cal formulas. AB 1312 took effect Jan. 1, 2026, but specified screening/presumptive duties begin July 1, 2027—do not present them as active in 2026.[S21] | High on dates and thresholds. |
| New York | Public Health Law §2807-k(9-a); NY Department of Health[S22] | Eligible uninsured and underinsured patients through 400% FPL. | All hospitals; uniform application, underinsured protection when 12-month out-of-pocket cost exceeds 10% of income, and no immigration-status eligibility criterion. Revised rules effective Oct. 20, 2024.[S22] | High. |
| Illinois | Hospital Uninsured Patient Discount Act, 210 ILCS 89/10; Fair Patient Billing Act, 210 ILCS 88[S23][S24] | Free care for uninsured patients ≤200% FPL; discount availability extends to 600% FPL at non-rural hospitals and 300% at rural/critical-access hospitals. | All covered hospitals; annual collection cap is 20% of family income after the discount. Screening duties constrain billing while assistance eligibility is evaluated.[S23][S24] | High. |
| Maryland | Health-General §19-214.1[S25] | Free care ≤200%; standard reductions: 75% at 201–250% and 60% at 251–300%. Financial-hardship tiers continue through 500% where debt exceeds the statutory income share. | Regulated acute/chronic hospitals; uniform application, 240-day period, appeals, presumptive categories such as SNAP/WIC/energy assistance/free lunch, and limited asset testing above a statutory level.[S25] | High; detailed implementation should use the current Commission materials. |
| Colorado | HB 21-1198 and Hospital Discounted Care Manual[S26] | Screening and discounted-care protections at ≤250% FPL; no asset test. | Hospitals and licensed health-care professionals. Current manual caps monthly payment plans at 4% of gross monthly income for facility-only bills, 6% combined, and 2% for separately billed professionals.[S26] | High for statute/manual; verify annual manual revisions. |
| Oregon | ORS 442.614–.615[S27] | Nonprofit hospitals: free ≤200%; minimum 75% discount at 201–300%, 50% at 301–350%, and 25% at 351–400%. | Nonprofit hospitals and nonprofit affiliates; insured patients can qualify. Prescreening and appeals can pause specified collection activity.[S14][S27] | High. |
| New Jersey | Charity Care Program, N.J. Department of Health[S28] | Free ≤200%; patient share is 20%, 40%, 60%, or 80% in successive bands through 300%. | Acute-care hospitals; uninsured/partially insured residents who lack other coverage. Asset limits are $7,500 individual/$15,000 family; additional help applies when bills exceed 30% of income.[S28] | High; state program page current when accessed. |
| Nevada | NRS 439B.320[S29] | No universal individual FPL entitlement comparable with Washington/Oregon; the statute sets aggregate indigent inpatient-care obligations tied to prior-year net revenue. | Covered hospitals coordinate indigent inpatient care with counties. BillBack must not translate this aggregate obligation into a guaranteed personal discount.[S29] | High on limitation. |
| Connecticut | Conn. Gen. Stat. §19a-673; Office of the Healthcare Advocate guidance[S30] | Uninsured patients at ≤250% FPL, after Medicaid ineligibility, cannot be collected more than the hospital’s cost. | Licensed hospitals and related collection agents; it is a cost cap, not a blanket statewide free-care schedule. Additional underinsured protections require case-specific review.[S30] | High on baseline; medium on individual application without current counsel review. |
| Minnesota | Minn. Stat. §§144.587, 144.589[S31] | No uniform statewide free-care FPL schedule. The 2026 charge cap applies to qualifying uninsured households under $125,000 and uses the lowest contracted nongovernmental reimbursement measure. | Private/nonprofit/municipal hospitals must screen uninsured or unknown-coverage patients, assist potentially eligible people, and restrict collection/payment-plan/credit steps while screening is pending. | High. Do not generalize one system’s settlement thresholds statewide. |

## 2.3 Medical debt and credit reporting: current status

The CFPB finalized a federal rule on January 14, 2025 that would have removed medical debt information from creditor underwriting and consumer reports. A federal district court vacated the rule on July 11, 2025; therefore the rule is **not in effect** as of November 22, 2026. Confidence is **high**, based on the final rule, judgment, and CFPB’s subsequent consumer guidance.[S32][S33][S34]

Separate nationwide credit-bureau policies generally exclude paid medical collections, collections less than a year old, and unpaid medical collections with an initial reported balance below $500; CFPB’s September 2025 guidance explains that unpaid debt older than 365 days and over $500 could still appear. Those are industry policies, not the vacated CFPB rule, and a consumer’s actual reports must be checked.[S34]

Selected enacted state changes include Washington’s 2025 law restricting furnishing/reporting medical debt, Maryland’s 2025 collection and reporting guidance, and Oregon’s 2025 chapter 343; New York’s Fair Medical Debt Reporting Act took effect in December 2023, California’s AB 2297/SB 1061 protections took effect in 2025, and Minnesota’s 2024 Debt Fairness Act bars medical-debt reporting. These examples are not exhaustive, can interact with federal preemption questions, and should be maintained as dated jurisdiction rules rather than hard-coded slogans.[S35][S36][S37][S38][S21][S39]

## 2.4 Product legal and privacy risks

| Risk | Finding | Design control |
|---|---|---|
| Unauthorized practice of law (UPL) | State definitions and enforcement differ. Personalized advice about a specific legal right, negotiation, or court process is riskier than publishing sourced information or user-controlled forms; some states regulate document-preparation services.[S40] | Counsel-led 50-state review; fixed sourced logic; explain uncertainty; user reviews and sends; no representation or outcome guarantee; route disputes, suits, garnishments, and imminent deadlines to legal aid. |
| HIPAA scope | HIPAA applies to covered entities and business associates. A direct-to-consumer app is not automatically covered merely because it handles health data; acting for a provider/plan can change the analysis and require a business-associate agreement.[S41] | Do not say “HIPAA applies” or “HIPAA compliant” without role/contract analysis. Apply strong safeguards regardless and reassess for each institutional integration. |
| FTC Health Breach Notification Rule | The FTC’s amended rule, effective July 29, 2024, expressly addresses health apps and unauthorized disclosures by entities not covered by HIPAA; covered breaches can require notice to people, the FTC, and sometimes media.[S42] | Incident plan, vendor inventory, consent logging, access controls, notification workflow, and no hidden advertising/analytics disclosures. |
| State consumer-health privacy | Washington’s My Health My Data Act requires notices and consents for consumer-health data collection/sharing, separate sale authorization, deletion, and geofence restrictions; Nevada and Connecticut also regulate sensitive/consumer health data.[S43][S44][S45] | Minimize collection, separate consent, prohibit sale/targeted advertising, support access/deletion, set retention limits, and conduct a state-law applicability matrix. |
| Misleading promises | “Nothing is stored,” “collections are paused,” “you qualify,” or “this will remove the debt” can be false depending on logs, vendors, law, and adjudicator action. | Use “likely” only with evidence; state what is stored and for how long; distinguish request from legal effect; provide dated citations and escalation. |

# 3. Competitors and partners

## 3.1 Direct, adjacent, and hospital-side competitors

| Organization/product | What it does / who pays | Verified scale or status | How BillBack differs |
|---|---|---|---|
| Dollar For | Nonprofit consumer education and high-touch FAP application assistance; free to patients and supported by philanthropy/donations. | Peer-reviewed 2024 paper reports 17,000+ applications and $60M+ relief since 2019; a January 2026 partner article says 36,000 patients and $120M, but that later figure is a secondary report.[S11][S46] | Dollar For validates the need and manual workflow. BillBack’s wedge is instant evidence-linked facility/policy matching and user-controlled documents; partnership is more sensible than claiming it is absent. |
| Undue Medical Debt (formerly RIP Medical Debt) | Nonprofit buys or receives portfolios and automatically abolishes qualifying debt; people do not apply for individual relief. | Its 2025 impact report, published May 2026, reports a cumulative $30B milestone; a November 2026 official partner release says more than $53B since 2014. These are organization/partner claims, not independently audited here.[S47][S48] | Downstream portfolio relief versus upstream prevention/application assistance. |
| Goodbill | Audits bills and negotiates; consumer pricing is 20% of accepted savings, capped at $1,000, according to its help page. | Current client count/results were not independently verified.[S49] | Paid savings model and negotiation versus a free eligibility/application workflow. |
| Resolve | Medical-bill advocacy and negotiation. | Current pricing, caseload, and outcomes were not independently verified; the official landing page is promotional.[S50] | Human/negotiation service versus transparent self-service assistance. |
| CoPatient | Historically offered bill review/negotiation. | Current ownership, active product, pricing, and scale are **unverified**; no adequate current primary source was found. | Treat as a market precedent, not a current benchmark. |
| Medical Billing Advocates of America | Training and advocate directory; its current site says consumer cases are temporarily unavailable. | Directory/training scale and outcomes are unverified.[S51] | Network/referral possibility; BillBack is a product and evidence layer, not a professional credential. |
| Experian Health Patient Financial Clearance | Hospital-side screening using income/employment verification for Medicaid and financial assistance. Hospital/provider pays. | Experian announced integrated verification in October 2026; performance and installed-base figures were not independently verified.[S52] | Revenue-cycle workflow for providers versus patient-controlled public-interest workflow. TransUnion/Change Healthcare product status requires procurement verification before comparison. |

## 3.2 AI-era medical-bill tools found in 2025–2026

Unbill says it compares EOBs, bills, and denials and prepares disputes, with an employer/enterprise orientation; Salud announced a free consumer app and expert review for a fall 2026 launch; SemiCare and Lapius advertise upload-and-review or negotiation workflows; Parlio describes AI help for health-care charges; and ProjectLeo announced a broader AI patient advocate in June 2026.[S53][S54][S55][S56][S57][S58] For all six, current active-user counts, accuracy, outcome rates, and (except where the official site clearly states otherwise) pricing remain **unverified**. Vendor pages and press releases establish positioning, not effectiveness.

BillBack’s defensible differentiation is therefore not “first AI medical-bill assistant.” It is a narrower and auditable claim: deterministic eligibility against a facility-specific, source-linked rule; a state-law overlay; minimal data retention; editable patient-controlled outputs; and a visible boundary between information, automated screening, and professional help.

## 3.3 Realistic distribution and service partners

| Partner | Why it fits | Practical pilot |
|---|---|---|
| Legal aid and consumer-law clinics | Can handle UPL-sensitive denials, suits, garnishment, and credit disputes. CFPB directs consumers with debt problems to legal aid.[S59] | Referral protocol with urgency flags and a complete source/evidence packet. |
| 211 networks | 211 reports service coverage for 99% of the U.S. population.[S60] | Train navigators; localized link/referral integration; feedback on missing programs. |
| Federally qualified health centers | HRSA reports roughly 1,400 health centers, 16,600 service sites, and 32.7M patients; HRSA data say about 90% of patients are at or below 200% FPL.[S61] | Discharge/referral pilot and benefit screening, with privacy boundaries. |
| Hospital financial counselors | Direct route to correct forms and missing-document resolution, but the hospital also has a collection interest. | Co-design only with conflict controls, published rules, and no hospital ability to suppress results. |
| Patient advocates and community health workers | Trusted assistance for language, disability, and documentation barriers. | Caseworker dashboard with consent, role-based access, and auditable handoff. |
| Credit unions, employers, and unions | Insured people still incur hospital debt: 63.5% of surveyed adults with past-due hospital debt incurred all of it while insured.[S62] | Sponsor distribution as a benefit; ban access to individual case data. |
| Libraries | Private device access, printing/scanning, and navigator space can address the digital divide. | Kiosk/privacy pilot with no local persistence and clear screen clearing; do not require librarian legal advice. |

# 4. Product expansion ideas, ranked

Ranking weighs impact, closeness to the current wedge, evidence, safety, and dependency burden. Effort is relative: **S** under a focused sprint, **M** multi-sprint/data integration, **L** sustained product/legal/partner work.

| Rank | Idea | Evidence it matters | Effort | Dependencies | Principal risk and control |
|---:|---|---|:---:|---|---|
| 1 | Nationwide policy coverage + state-law overlay | 2,770 nonprofit-hospital policies were needed to cover 92% of that sector in 2024; the new HospitalAid dataset shows both a tractable starting point and remaining evidence gaps.[S10][S11] | L | CMS/IRS pipeline, policy crawler, reviewer queue, counsel | A wrong facility or stale threshold harms users. Require provenance, effective dates, confidence, and human conflict review. |
| 2 | Insured-patient EOB/bill reconciliation and itemized-bill requests | 63.5% of adults with past-due hospital debt in the Urban survey incurred it while insured. Commonwealth Fund found 45% of insured working-age adults received a bill/copay they thought should have been covered, but this measures perceived coverage problems, not audited errors.[S62][S63] | M | Bill/EOB schemas, insurer vocabulary, privacy controls | False “error” accusations. Label discrepancies, explain possibilities, request itemization, and keep a human in the decision. |
| 3 | Follow-up tracker, completion checks, denial appeals, and collection-hold requests | §501(r)(6) gives complete/incomplete applications procedural effects during the 240-day period and requires reasonable efforts before ECAs.[S18] | M | Deadline engine, notification consent, state rules, delivery evidence | A reminder can imply a legal deadline or hold that does not apply. Date every rule; say “request,” not “guarantee.” |
| 4 | Presumptive eligibility + retroactive Medicaid routing | Maryland lists categorical presumptive pathways; Oregon requires prescreening; California has future screening duties beginning July 1, 2027. Medicaid retroactivity can cover prior months, but federal changes scheduled for Jan. 1, 2027 shorten the maximum look-back for specified groups and states/waivers vary.[S21][S25][S27][S64] | L | State program rules, eligibility partner, effective-date engine | High-stakes eligibility and rapid statutory change. Screen and refer; do not adjudicate or promise coverage. |
| 5 | Multilingual, accessible outputs | IRS translation rules show language access is part of FAP publication, and hospital documents can still be difficult to navigate.[S9] | M | Certified translation, locale-specific QA, accessibility testing | Machine translation can change legal/financial meaning. Human-review core templates and show controlling source. |
| 6 | Caseworker dashboard | FQHC and 211 reach make assisted use a plausible scaling channel.[S60][S61] | M | Consent/delegation, RBAC, audit logs, partner training | Shared access expands breach and coercion risk. Least privilege, explicit case consent, automatic expiry. |
| 7 | SMS/WhatsApp reminders | Follow-up friction is real, but this research found no credible national causal estimate specific to FAP completion. | M | Messaging vendor, consent, localization | Sensitive content on shared devices and vendor retention. Use neutral messages, opt-in, minimal metadata. |
| 8 | Offline/library kiosk | Libraries can supply access and printing; exact current national kiosk need is unverified. | M | Secure local session, printing/scanning, partner operations | Residual files and shoulder-surfing. Ephemeral sessions, secure deletion, privacy screens, staff protocol. |
| 9 | Public policy compliance checker/scorecard | Lown’s 2026 fair-share analysis covers 3,037 hospitals, showing public benchmarking demand; Schedule H and live-policy conflicts create testable compliance questions.[S15] | L | National dataset maturity, legal review, methodology governance | Defamation/false compliance claims. Publish criteria/evidence, allow response/correction, distinguish document check from legal finding. |
| 10 | Hospital price-transparency comparator | CMS requires hospitals to publish machine-readable standard charges and consumer-friendly information for 300 shoppable services; CMS cautions that listed rates are not a person’s guaranteed out-of-pocket amount.[S65][S66] | L | Code/unit/setting matching, payer/plan context, MRF ingestion | A rate comparison can mislabel legitimate differences. Start as evidence for review, not “overcharge detected.” |
| 11 | Credit-report dispute drafts | Accurate medical debt can still appear under current federal/bureau rules, while state bans vary.[S34][S35][S36][S37] | M | Report intake, FCRA/state-law counsel, identity workflow | Encouraging frivolous disputes or promising deletion. Generate only evidence-based inaccuracy/illegality disputes and refer contested cases. |

### Billing-error evidence: what can safely be said

KFF’s 2022 survey found that 43% of adults, and 53% of adults with health-care debt, said they had received a bill they *thought* contained an error. That is a perceived-error measure, not an audit of medical bills.[S67] Commonwealth Fund’s 2024 survey similarly measured unexpected bills and perceived coverage denials, not a verified coding-error rate.[S63] BillBack should not repeat “80% of medical bills contain errors”; this research did not find a credible national primary source for it.

# 5. Impact and sustainability

## 5.1 Size and shape of the problem

| Measure | Best current evidence | Interpretation |
|---|---|---|
| Prevalence | 26.6% of adults reported family medical debt in December 2025; 15.4% reported debt past due or unpayable.[S68] | Broad problem, including insured households. Survey definition and time point should accompany the number. |
| Severity/collections | Among respondents with debt, 53.8% owed ≥$1,000, 15.5% ≥$5,000, 35.2% had collection contact, and 21.7% reported a lower credit score.[S68] | Prioritize collection prevention and outcome tracking, not just document generation. |
| Hospital share | 72.9% of adults with past-due medical debt reported owing hospitals; 60.9% of those with hospital debt reported a collection agency.[S62] | Hospital FAPs are a well-targeted wedge, though not the entire debt market. |
| Aggregate debt | KFF’s interpretation of 2023 Census SIPP estimates at least $200B in medical debt.[S69] | Use “at least $200B,” not an unsupported $220B. Different surveys/definitions produce different totals. |
| Assistance leakage | Hospitals reported $2.7B in bad debt attributable to patients probably eligible for assistance across the sampled nonprofit organizations; self-reporting likely understates or inconsistently identifies it.[S70] | Direct evidence for better screening/application, but not a complete national eligibility-loss estimate. |
| Proven intervention scale | Dollar For’s peer-reviewed report described 17,000+ applications and $60M+ facilitated relief since 2019.[S11] | Human assistance can yield relief; BillBack still needs its own prospective outcome study. |

Relief face value is not the same as improved well-being. A randomized study of $169M in medical-debt abolition for 83,401 people found no average improvement in measured credit, financial distress, health-care utilization, or mental health over the study period. The result does not test FAP application assistance, but it is a strong reason to measure lived and financial outcomes, not only nominal dollars.[S71]

## 5.2 Sustainable funding options

| Model | Fit | Guardrails |
|---|---|---|
| Philanthropic grants | Strong fit for initial data infrastructure, legal review, evaluation, and free patient access. Arnold Ventures reports health-care affordability/evidence funding and directly funded medical-debt/hospital-market research; RWJF publishes and funds affordability research.[S72][S73] | Avoid building permanent operations around a one-year grant; fund reusable public data and rigorous evaluation. |
| Independent nonprofit/donations | Aligns patient trust and free service; Dollar For and Undue demonstrate recognizable nonprofit models.[S11][S47] | Transparent finances, conflict policy, independent board, published methodology, no data sale. |
| Sponsored distribution (employers, unions, credit unions) | Reaches insured and underinsured people while keeping patient access free.[S62] | Sponsor receives aggregate metrics only; no individual case access or eligibility influence. |
| API/data licensing | Evidence-linked policy data can support legal aid, navigators, benefits teams, and researchers. | Preserve a free patient product and public correction channel; respect source licenses; do not license sensitive user data. |
| Government/regulator/hospital compliance contracts | Could fund policy normalization, screening quality, and public reporting. | Structural conflict: separate patient logic/governance, disclose funders, publish criteria, never let a hospital suppress a result. |
| Patient contingency fee | Poor fit for the target population despite use by some advocates.[S49] | Do not prioritize; it can reduce relief and bias recommendations toward negotiable bills. |

## 5.3 Impact measurement plan

Use a prospective funnel with denominators and time windows:

1. **Reach:** unique screenings, matched facilities, languages, states, referral channel, and assisted versus self-service use.
2. **Data quality:** facility-match confirmation, field-level reviewed accuracy, policy age, broken-link rate, policy/Schedule H/state-law conflict rate, and correction time.
3. **Process:** eligible/possibly eligible screens; applications started, submitted, deemed complete, appealed, and pending; median time to each stage; missing-document causes.
4. **Decisions:** approval/partial approval/denial rates by hospital and pathway, with unresolved cases retained in denominators and confidence intervals for comparisons.
5. **Financial outcomes:** verified amount forgiven, discounted, refunded, or covered by Medicaid/insurance; patient out-of-pocket avoided; payment-plan change. Report face value separately from realized cash benefit.
6. **Protection outcomes:** ECAs/collection contacts stopped, lawsuits or garnishments referred, inaccurate credit items corrected, and care access restored—only with documentation and without claiming causation from a simple before/after count.
7. **Equity and safety:** outcomes by language, insurance, income band, disability/access mode, geography, and race/ethnicity only when voluntarily provided and safely governed; privacy incidents, incorrect recommendations, escalations, complaints, and appeal reversals.
8. **Evaluation:** begin with an audited cohort and independent chart/document review, then use randomized or stepped-wedge outreach where ethical. Compare automated assistance plus normal services with normal services, not with “no help,” and pre-register primary outcomes.

## Sources

All web sources were accessed **November 22, 2026** unless another access date is stated. “Undated” means the publisher did not display a publication date; the access date is supplied rather than inventing one.

- **[S1]** Internal Revenue Service, *2025 Instructions for Schedule H (Form 990)*, 2025. <https://www.irs.gov/instructions/i990sh>
- **[S2]** Internal Revenue Service, *Form 990 Series Downloads*, undated/current 2026 release page. <https://www.irs.gov/charities-non-profits/form-990-series-downloads>
- **[S3]** Internal Revenue Service, *Tax Exempt Organization Search Bulk Data Downloads*, reviewed May 19, 2026, and *TEOS FAQs*, undated. <https://www.irs.gov/charities-non-profits/tax-exempt-organization-search-bulk-data-downloads> and <https://www.irs.gov/charities-non-profits/tax-exempt-organization-search-teos-faqs>
- **[S4]** ProPublica, *Nonprofit Explorer API v2*, undated/current documentation. <https://projects.propublica.org/nonprofits/api>
- **[S5]** Centers for Medicare & Medicaid Services, *Hospital General Information*, modified October 26, 2026; released November 12, 2026. <https://data.cms.gov/provider-data/dataset/xubh-q36u>
- **[S6]** Centers for Medicare & Medicaid Services, *QIES Provider of Services Methodology*, December 2025. <https://data.cms.gov/sites/default/files/2025-12/QIES%20POS%20methodology.pdf>
- **[S7]** Centers for Medicare & Medicaid Services, *NPPES Data Dissemination*, monthly file dated November 9, 2026; data-dissemination readme, publication date not displayed. <https://download.cms.gov/nppes/NPI_Files.html> and <https://edit.cms.gov/Regulations-and-Guidance/Administrative-Simplification/NationalProvIdentStand/Downloads/Data_Dissemination_File-Readme.pdf>
- **[S8]** American Hospital Association, *AHA Annual Survey Database* and methodology, undated/current product pages. <https://www.ahadata.com/aha-annual-survey-database> and <https://www.ahadata.com/aha-hospital-data-methodology>
- **[S9]** Internal Revenue Service, *Financial Assistance Policy and Emergency Medical Care Policy—Section 501(r)(4)*, undated/current guidance. <https://www.irs.gov/charities-non-profits/financial-assistance-policy-and-emergency-medical-care-policy-section-501r4>
- **[S10]** HospitalAid, *Open Data*, version published November 21, 2026. <https://hospitalaid.org/open-data/>
- **[S11]** McGarry et al., *US Nonprofit Hospitals’ Financial Assistance Policies, 2024*, *Health Affairs Scholar*, November 2024; PubMed Central version posted 2025. <https://pmc.ncbi.nlm.nih.gov/articles/PMC12230784/>
- **[S12]** California Department of Health Care Access and Information, *Hospital Fair Pricing Policy Lookup*, undated/current. <https://www.syfphr.oshpd.ca.gov/>
- **[S13]** Washington State Department of Health, *Hospital Patient Information and Charity Care*, undated/current. <https://doh.wa.gov/data-and-statistical-reports/healthcare-washington/hospital-and-patient-data/hospital-patient-information-and-charity-care>
- **[S14]** Oregon Department of Consumer and Business Services, *Financial Assistance Programs*, undated/current. <https://healthcare.oregon.gov/Pages/assistance-programs.aspx>
- **[S15]** Lown Institute, *Hospital Fair Share Spending 2026*, 2026. <https://lownhospitalsindex.org/hospital-fair-share-spending-2026/>
- **[S16]** U.S. Government Publishing Office, *26 CFR Part 1, §§1.501(r)-4 through -6*, 2025 edition. <https://www.govinfo.gov/content/pkg/CFR-2025-title26-vol9/xhtml/CFR-2025-title26-vol9-part1.html>
- **[S17]** Internal Revenue Service, *Limitation on Charges—Section 501(r)(5)*, undated/current guidance. <https://www.irs.gov/charities-non-profits/limitation-on-charges-section-501r5>
- **[S18]** Internal Revenue Service, *Billing and Collections—Section 501(r)(6)*, undated/current guidance. <https://www.irs.gov/charities-non-profits/billing-and-collections-section-501r6>
- **[S19]** Washington State Legislature, *RCW 70.170.060*, current codification; publication date not displayed. <https://app.leg.wa.gov/rcw/default.aspx?cite=70.170.060>
- **[S20]** California HCAI, *Hospital Bill Complaint Program FAQ*, current page; publication date not displayed. <https://hcai.ca.gov/affordability/hospital-fair-billing-program/hospital-bill-complaint-program/frequently-asked-questions/>
- **[S21]** California HCAI, *Hospital Fair Billing Program Laws and Regulations*, updated for 2025–2026 enactments; page publication date not displayed. <https://hcai.ca.gov/affordability/hospital-fair-billing-program/laws-and-regulations/>
- **[S22]** New York State Department of Health, *Hospital Financial Assistance Law*, revised rules effective October 20, 2024; current page publication date not displayed. <https://www.health.ny.gov/facilities/hospital/financial_assist/index.htm>
- **[S23]** Illinois General Assembly, *210 ILCS 89/10*, current codification; publication date not displayed. <https://ilga.gov/legislation/ilcs/fulltext?DocName=021000890K10>
- **[S24]** Illinois General Assembly, *Fair Patient Billing Act, 210 ILCS 88*, current codification; publication date not displayed. <https://www.ilga.gov/Legislation/ILCS/Articles?actid=2798&chapterid=21>
- **[S25]** Maryland General Assembly, *Health-General §19-214.1*, current codification; publication date not displayed. <https://mgaleg.maryland.gov/mgawebsite/Laws/StatuteText?article=ghg&section=19-214.1>
- **[S26]** Colorado General Assembly, *HB21-1198*, enacted 2021; Colorado Department of Health Care Policy & Financing, *2024–25 Hospital Discounted Care Manual*, 2024. <https://leg.colorado.gov/bills/HB21-1198> and <https://hcpf.colorado.gov/sites/hcpf/files/2024-25%20%283%29%20Hospital%20Discounted%20Care%20Manual.pdf>
- **[S27]** Oregon Legislature, *ORS 442.614–442.615*, 2025 edition/current codification. <https://www.oregonlegislature.gov/bills_laws/ors/ors442.html?ID=18000>
- **[S28]** New Jersey Department of Health, *Charity Care—Overview*, undated/current. <https://nj.gov/health/hcf/charity-care/overview/>
- **[S29]** Nevada Legislature, *NRS 439B.320*, current codification; publication date not displayed. <https://www.leg.state.nv.us/division/Legal/LawLibrary/NRS/NRS-439B.html>
- **[S30]** Connecticut General Assembly, *Conn. Gen. Stat. §19a-673*, 2026 codification; Connecticut Office of the Healthcare Advocate, *Medical Debt Rules in Connecticut*, September 2026. <https://www.cga.ct.gov/current/pub/chap_368z.htm> and <https://portal.ct.gov/oha/knowledge-base/articles/health-insurance/medical-bills-and-debt/medical-debt-rules-in-connecticut>
- **[S31]** Minnesota Revisor of Statutes, *Minn. Stat. §§144.587 and 144.589*, 2026 codification. <https://www.revisor.mn.gov/statutes/cite/144.587> and <https://www.revisor.mn.gov/statutes/2026/cite/144.589>
- **[S32]** Consumer Financial Protection Bureau, *Prohibition on Creditors and Consumer Reporting Agencies Concerning Medical Information*, final rule, *Federal Register*, January 14, 2025. <https://www.govinfo.gov/content/pkg/FR-2025-01-14/pdf/2024-30824.pdf>
- **[S33]** U.S. District Court for the Eastern District of Texas, *Cornerstone Credit Union League v. CFPB*, judgment/order vacating rule, July 11, 2025. <https://www.govinfo.gov/content/pkg/USCOURTS-txed-4_25-cv-00016/pdf/USCOURTS-txed-4_25-cv-00016-0.pdf>
- **[S34]** Consumer Financial Protection Bureau, *Do medical bills affect my credit?*, reviewed September 5, 2025; Equifax, *What have the Nationwide Credit Reporting Agencies changed?*, current page describing changes effective July 2022/April 2023, publication date not displayed. <https://www.consumerfinance.gov/ask-cfpb/do-medical-bills-affect-my-credit-and-where-do-i-find-out-whats-in-my-medical-payment-history-en-1837/> and <https://www.equifax.com/personal/help/article-list/-/h/a/what-are-nationwide-credit-reporting-agencies-ncra-changing-on-consumer-credit-files/>
- **[S35]** Washington State Legislature, *2025 Session Laws, chapter 145 (ESSB 5480)*, 2025. <https://lawfilesext.leg.wa.gov/biennium/2025-26/Htm/Bills/Session%20Laws/Senate/5480-S.SL.htm>
- **[S36]** Maryland Department of Labor, *Advisory Guidance on Collection of Medical Debt*, 2025. <https://www.labor.maryland.gov/finance/advisories/advisory-guidancecollectionmedicaldebt.pdf>
- **[S37]** Oregon Legislature, *2025 Oregon Laws, chapter 343*, 2025. <https://www.oregonlegislature.gov/bills_laws/lawsstatutes/2025orlaw0343.pdf>
- **[S38]** New York Attorney General, *Medical Debt Reporting*, May 2026 guidance describing the Fair Medical Debt Reporting Act. <https://ag.ny.gov/resources/individuals/health-care-insurance/Reporting-medical-debt>
- **[S39]** Minnesota Attorney General, *Hendricks settlement announcement*, November 9, 2026, summarizing the 2024 Debt Fairness Act reporting ban. <https://ag.state.mn.us/Office/Communications/2026/11/09_Hendricks.asp>
- **[S40]** American Bar Association, *Lowering UPL Risk for Nonlawyer Legal Help*, July–August 2024; California State Bar, *Unauthorized Practice of Law Complaint*, undated/current. <https://www.americanbar.org/groups/law_practice/resources/law-practice-magazine/2024/july-august-2024/lowering-upl-risk-for-nonlawyer-legal-help/> and <https://www.calbar.ca.gov/public/concerns-about-attorney/avoid-legal-services-fraud/unauthorized-practice-law-complaint>
- **[S41]** U.S. Department of Health and Human Services, *Covered Entities and Business Associates* and health-app developer scenarios, undated/current. <https://www.hhs.gov/hipaa/for-professionals/covered-entities/index.html> and <https://www.hhs.gov/sites/default/files/ocr-health-app-developer-scenarios-2-2016.pdf>
- **[S42]** Federal Trade Commission, *FTC Finalizes Changes to Health Breach Notification Rule*, April 26, 2024; rule effective July 29, 2024. <https://www.ftc.gov/news-events/news/press-releases/2024/04/ftc-finalizes-changes-health-breach-notification-rule>
- **[S43]** Washington State Legislature, *Chapter 19.373 RCW, My Health My Data Act*, current codification; phased effective dates in 2024. <https://app.leg.wa.gov/RCW/default.aspx?cite=19.373&full=true>
- **[S44]** Nevada Legislature, *NRS 603A.400–.550*, current codification; publication date not displayed. <https://www.leg.state.nv.us/nrs/nrs-603a.html>
- **[S45]** Connecticut General Assembly, *Chapter 743jj, Data Privacy and Online Monitoring*, 2026 supplement. <https://cga.ct.gov/2026/sup/chap_743jj.htm>
- **[S46]** HealthWell Foundation, *What Patients Don’t Know About Hospital Financial Assistance*, January 28, 2026. <https://www.healthwellfoundation.org/realworldhealthcare/what-patients-dont-know-about-hospital-financial-assistance-but-should/>
- **[S47]** Undue Medical Debt, *2025 Impact Report*, published May 2026. <https://unduemedicaldebt.org/wp-content/uploads/2026/05/Undue-Medical-Debt-2025-Impact-Report_Digital.pdf>
- **[S48]** UFC and Undue Medical Debt, partnership release, November 12, 2026. <https://www.ufc.com/news/ufc-partners-undue-medical-debt-help-eliminate-more-50-million-medical-debt-veterans>
- **[S49]** Goodbill, *FAQ* and *Pricing*, pricing page edited October 4, 2023; current pages. <https://www.goodbill.com/faq> and <https://help.goodbill.com/en/articles/254209>
- **[S50]** Resolve Medical Bills, current service page; publication date not displayed. <https://www.resolvemedicalbills.com/lp/medical-bill-advocate>
- **[S51]** Medical Billing Advocates of America, current home/directory page; publication date not displayed. <https://billadvocates.com/>
- **[S52]** Experian plc, *Experian Health Integrates Income and Employment Verification*, October 13, 2026. <https://www.experianplc.com/newsroom/press-releases/2026/experian-health-integrates-income-and-employment-verification-in>
- **[S53]** Unbill, current product page; publication date not displayed. <https://unbill.ai/>
- **[S54]** Salud, current press page; 2026 announcements. <https://salud.love/press>
- **[S55]** SemiCare, current product page; publication date not displayed. <https://semicare.app/>
- **[S56]** Lapius, current product page; publication date not displayed. <https://www.lapiusai.com/>
- **[S57]** Parlio, current product page; publication date not displayed. <https://www.parlio.ai/>
- **[S58]** ProjectLeo/PRNewswire, launch release republished by Yahoo Finance, June 24, 2026. <https://finance.yahoo.com/healthcare/articles/projectleo-launches-ai-patient-advocate-140800768.html>
- **[S59]** Consumer Financial Protection Bureau, *What should I do if I can’t pay a medical bill?*, current guidance; publication date not displayed. <https://www.consumerfinance.gov/ask-cfpb/what-should-i-do-if-i-cant-pay-a-medical-bill-en-2125/>
- **[S60]** 211, *Our Impact*, current page; publication date not displayed. <https://211.org/about-us/our-impact/>
- **[S61]** Health Resources and Services Administration, *About the Health Center Program* and health-center data, current 2025–2026 pages. <https://bphc.hrsa.gov/about-health-center-program> and <https://data.hrsa.gov/topics/health-centers/>
- **[S62]** Urban Institute, *Most Adults with Past-Due Medical Debt Owe Money to Hospitals*, March 2023. <https://www.urban.org/sites/default/files/2023-03/Most%20Adults%20with%20Past-Due%20Medical%20Debt%20Owe%20Money%20to%20Hospitals_0.pdf>
- **[S63]** Commonwealth Fund, *New Research: Insured Working-Age Americans Face Widespread Medical Billing Problems*, August 1, 2024. <https://www.commonwealthfund.org/press-release/2024/new-research-insured-working-age-americans-face-widespread-medical-billing>
- **[S64]** CMS, *Eligibility and Enrollment Rules*, current 2026 resource; KFF, *Health Provisions in the 2025 Federal Budget Reconciliation Law*, 2025/current update. <https://www.medicaid.gov/resources-for-states/downloads/eligibility-enrollment-rules.pdf> and <https://www.kff.org/medicaid/health-provisions-in-the-2025-federal-budget-reconciliation-law/>
- **[S65]** Centers for Medicare & Medicaid Services, *Hospital Price Transparency*, March 2026. <https://www.cms.gov/files/document/mln7215754-hospital-price-transparency.pdf>
- **[S66]** Centers for Medicare & Medicaid Services, *Hospital Price Transparency Policy FAQs*, June 2026. <https://www.cms.gov/files/document/hpt-policy-faqs-june-2026.pdf>
- **[S67]** KFF, *Could Consumer Assistance Be Helpful to People Facing Medical Debt?*, July 14, 2022. <https://www.kff.org/private-insurance/could-consumer-assistance-be-helpful-to-people-facing-medical-debt/>
- **[S68]** Urban Institute, *More than One-Quarter of U.S. Adults Had Medical Debt in 2025*, October 6, 2026. <https://www.urban.org/research/publication/more-one-quarter-us-adults-had-medical-debt-2025>
- **[S69]** KFF, *Health Policy 101: Health Care Costs and Affordability*, current 2025–2026 page using 2023 Census SIPP; page publication date not displayed. <https://www.kff.org/health-costs/health-policy-101-health-care-costs-and-affordability/>
- **[S70]** KFF Health News, *Patients Eligible for Charity Care Instead Get Big Bills*, December 2019. <https://kffhealthnews.org/news/patients-eligible-for-charity-care-instead-get-big-bills/>
- **[S71]** Kluender et al., *The Effects of Randomized Medical Debt Relief*, working paper posted by CFPB, April 8, 2024. <https://files.consumerfinance.gov/f/documents/cfpb_kluender-effects-of-randomized-medical-debt-relief.pdf>
- **[S72]** Arnold Ventures, *Our 2025 Approach to Giving*, November 16, 2026; Laura and John Arnold Foundation 2025 Form 990-PF, published November 2026. <https://www.arnoldventures.org/stories/our-2025-approach-to-giving> and <https://assets.arnoldventures.org/uploads/LJAF_990-PF_2025-FORM.pdf>
- **[S73]** Robert Wood Johnson Foundation, *More than One-Quarter of U.S. Adults Had Medical Debt in 2025*, October 2, 2026. <https://beta.rwjf.org/en/insights/our-research/2026/10/more-than-one-quarter-of-us-adults-had-medical-debt-in-2025.html>

---

# BillBack expansion roadmap

**As of:** November 22, 2026  
**Effort:** S = focused sprint; M = several sprints/integration; L = sustained data, product, legal, or partner work.  
**Principle:** ship an auditable national evidence layer before broad negotiation features. All automated outputs remain likely assessments and editable user-controlled drafts, not legal advice or guaranteed outcomes.

## Next 2 weeks

### P0 — Freeze the demo evidence contract and QA 20 policies

- **What:** define one versioned record for facility identity, policy/effective/retrieval date, free threshold, discount tiers, insured/high-medical-cost treatment, asset/residency rules, deadline, application URL, covered-provider list, and exact page/line evidence. Double-review the 20 demo hospitals and publish field-level completeness rather than a single accuracy percentage.
- **Why/evidence:** Schedule H exposes broad FPG thresholds and criteria but not the full tier/application logic; the IRS requires multiple policy documents and a provider list. Sources: IRS, *2025 Schedule H Instructions* (2025) and §501(r)(4) guidance (undated/current), accessed Nov. 22, 2026: <https://www.irs.gov/instructions/i990sh> and <https://www.irs.gov/charities-non-profits/financial-assistance-policy-and-emergency-medical-care-policy-section-501r4>.
- **Effort:** S.
- **Dependencies:** second reviewer; adjudication checklist; policy snapshots.
- **Risk/control:** small-sample results may be mistaken for national accuracy. Call them demo QA, retain disagreements, and report denominators per field.

### P0 — Add a CMS facility identity table and explicit confirmation step

- **What:** use CCN, name, address, phone, type, and ownership from CMS Hospital General Information; normalize names/addresses; show the matched facility and ask the user to confirm when confidence is not decisive.
- **Why/evidence:** the CMS file is a current national facility roster; the Nov. 12, 2026 release has 5,435 rows. Source: CMS, modified Oct. 26/released Nov. 12, 2026; accessed Nov. 22, 2026: <https://data.cms.gov/provider-data/dataset/xubh-q36u>.
- **Effort:** S.
- **Dependencies:** download snapshot; normalization rules; bill-field mapping.
- **Risk/control:** parent system, facility, and professional group can be confused. Never auto-accept low-confidence matches; do not use NPI as proof of ownership.

### P0 — Prototype Schedule H cross-checking on the demo set

- **What:** fetch the latest IRS XML by EIN, parse Part I and Part V facility thresholds/criteria, preserve raw XML paths, and flag policy/filing conflicts. Do not replace the live policy with the filing.
- **Why/evidence:** IRS XML and index files are available in bulk and generally update monthly; Schedule H contains facility-specific threshold fields but can use zero/narrative answers. Sources: IRS, bulk pages reviewed May 19, 2026/current 2026 releases, accessed Nov. 22, 2026: <https://www.irs.gov/charities-non-profits/form-990-series-downloads> and <https://www.irs.gov/charities-non-profits/tax-exempt-organization-search-bulk-data-downloads>.
- **Effort:** S.
- **Dependencies:** EIN lookup; XML schema adapter for tested years; test fixtures.
- **Risk/control:** stale fiscal-year data and multi-facility filings. Display tax period/submission date and preserve the parent-to-facility relationship.

### P0 — Correct legal/safety language and privacy claims

- **What:** replace absolute claims with “likely” and “request”; distinguish ECA suspension from all billing contact; state actual retention/logging; add source/effective dates, high-stakes escalation, consent, and deletion controls to the product specification.
- **Why/evidence:** §501(r)(6) uses 120/240-day procedures and specifies ECA handling; HIPAA does not automatically cover a direct-to-consumer app, while the FTC Health Breach Notification Rule can. Sources: IRS, current §501(r)(6) guidance; HHS, undated/current HIPAA guidance; FTC, Apr. 26, 2024 rule announcement, all accessed Nov. 22, 2026: <https://www.irs.gov/charities-non-profits/billing-and-collections-section-501r6>, <https://www.hhs.gov/hipaa/for-professionals/covered-entities/index.html>, <https://www.ftc.gov/news-events/news/press-releases/2024/04/ftc-finalizes-changes-health-breach-notification-rule>.
- **Effort:** S for copy/spec; M for architecture changes.
- **Dependencies:** inventory of analytics, logs, OCR/model vendors, and file lifecycle; counsel review.
- **Risk/control:** an unverified “nothing stored” statement is deceptive. Test and document deletion across subprocessors before using it.

### P1 — Import HospitalAid only as an attributed seed

- **What:** evaluate and import its CC BY 4.0 release into a quarantined candidate table; compare every demo record; keep BillBack evidence, retrieval dates, and corrections separate.
- **Why/evidence:** HospitalAid’s Nov. 21, 2026 release reports 3,496 hospitals and policy/Schedule H/state evidence, making it the fastest open breadth accelerator. Source: HospitalAid, Nov. 21, 2026; accessed Nov. 22, 2026: <https://hospitalaid.org/open-data/>.
- **Effort:** S.
- **Dependencies:** license attribution; schema mapping; deduplication; review sample.
- **Risk/control:** a new external dataset can contain errors or change availability. Pin versions, attribute, validate, and retain reproducible upstream sources.

### P1 — Define the outcome funnel before launch

- **What:** instrument match confirmed → eligibility result → application started/submitted/complete → decision/appeal → verified forgiveness/refund/coverage and time to resolution. Keep unresolved cases in denominators; separate face-value relief from realized out-of-pocket benefit.
- **Why/evidence:** randomized debt relief of $169M for 83,401 people did not improve average measured financial/health outcomes, showing why nominal dollars alone are insufficient. Source: Kluender et al., *The Effects of Randomized Medical Debt Relief*, Apr. 8, 2024; accessed Nov. 22, 2026: <https://files.consumerfinance.gov/f/documents/cfpb_kluender-effects-of-randomized-medical-debt-relief.pdf>.
- **Effort:** S for event/outcome specification; M for follow-up verification.
- **Dependencies:** consent, minimal analytics, follow-up process, privacy review.
- **Risk/control:** self-reported savings and attrition bias. Request documentary confirmation, label self-report, and publish follow-up rates.

## Next 3 months

### P0 — Build national policy ingestion and a reviewer queue

- **What:** combine CMS facilities, IRS XML, live FAP/application/summary/provider-list discovery, attributed seed data, content hashing, change detection, and reviewer reconciliation. Release facility/field coverage and freshness dashboards.
- **Why/evidence:** Dollar For’s published method used quarterly automated checks plus two-reviewer consensus and covered 2,770 hospitals/92% of private nonprofit hospitals by Mar. 14, 2024. Source: McGarry et al., *Health Affairs Scholar*, Nov. 2024 (PMC 2025); accessed Nov. 22, 2026: <https://pmc.ncbi.nlm.nih.gov/articles/PMC12230784/>.
- **Effort:** L.
- **Dependencies:** data model, crawler, PDF/OCR pipeline, reviewers, correction channel, state repositories.
- **Risk/control:** silent staleness and false joins. Hash/check quarterly, re-review identity/threshold changes, and block patient-ready status when required evidence is missing.

### P0 — Implement the first state-law rules with counsel sign-off

- **What:** date-version Washington, California, New York, Illinois, Maryland, Colorado, Oregon, and New Jersey thresholds and procedural rights; model Nevada, Connecticut, and Minnesota as narrower/different protections instead of inventing uniform free-care entitlements.
- **Why/evidence:** these states have materially different statutory thresholds, coverage, caps, screening, or presumptive pathways. Primary current citations are collected in [expansion-report.md](#22-state-charity-care-protections-beyond-the-federal-floor).
- **Effort:** L.
- **Dependencies:** health/consumer-law counsel, effective-date engine, annual legislative monitoring, test cases.
- **Risk/control:** law changes and scope ambiguity. Preserve enacted/effective dates, jurisdiction, hospital type, professional-bill scope, and counsel approval; never infer residency from a bill.

### P0 — Pilot insured-patient EOB/bill reconciliation

- **What:** extract bill and EOB values; identify—not adjudicate—patient-responsibility mismatches, duplicate-looking lines, missing adjustments, and absent itemization; produce a question/checklist and itemized-bill or insurer-review request.
- **Why/evidence:** 63.5% of adults with past-due hospital debt in a June 2022 survey incurred all of it while insured. Source: Urban Institute, Mar. 2023; accessed Nov. 22, 2026: <https://www.urban.org/sites/default/files/2023-03/Most%20Adults%20with%20Past-Due%20Medical%20Debt%20Owe%20Money%20to%20Hospitals_0.pdf>.
- **Effort:** M.
- **Dependencies:** EOB schemas, plan-language glossary, secure multi-document handling, expert review.
- **Risk/control:** a discrepancy is not necessarily an error. Use neutral phrasing, show source values, and never state the bill is invalid without corroboration.

### P0 — Add deadline-aware completion, follow-up, and appeal support

- **What:** generate document checklists, delivery proof, neutral 30/60-day reminders, application-status requests, missing-document responses, denial-reason capture, appeal drafts, and legal-aid escalation. Generate a collection-hold *request* and explain when federal/state suspension rules may apply.
- **Why/evidence:** §501(r)(6) requires reasonable efforts, recognizes complete/incomplete applications within a 240-day application period, and regulates ECAs. Source: IRS, undated/current guidance; accessed Nov. 22, 2026: <https://www.irs.gov/charities-non-profits/billing-and-collections-section-501r6>.
- **Effort:** M.
- **Dependencies:** policy/state deadlines, messaging consent, document status model, legal-aid network.
- **Risk/control:** reminders may create false confidence or disclose sensitive facts. Date rules, use neutral notifications, provide opt-out, and escalate imminent suits/garnishment.

### P1 — Public-benefit and retroactive-Medicaid referral pilot

- **What:** screen for possible Medicaid/CHIP and policy-listed presumptive categories, then hand off to an official enrollment channel; preserve service dates so a trained assister can assess retroactive coverage.
- **Why/evidence:** Maryland statute includes categorical presumptive eligibility, Oregon requires prescreening, and California’s additional duties begin July 1, 2027. Federal retroactivity rules are scheduled to narrow for specified groups on Jan. 1, 2027 and state waivers differ. Sources: Maryland General Assembly, current §19-214.1; Oregon ORS 442; California HCAI, current laws page; CMS/KFF current 2026 guidance, accessed Nov. 22, 2026: <https://mgaleg.maryland.gov/mgawebsite/Laws/StatuteText?article=ghg&section=19-214.1>, <https://www.oregonlegislature.gov/bills_laws/ors/ors442.html?ID=18000>, <https://hcai.ca.gov/affordability/hospital-fair-billing-program/laws-and-regulations/>, <https://www.medicaid.gov/resources-for-states/downloads/eligibility-enrollment-rules.pdf>.
- **Effort:** L.
- **Dependencies:** state/effective-date rules, enrollment partners, immigration-sensitive privacy design.
- **Risk/control:** inaccurate eligibility or immigration chilling effects. Ask only necessary questions, screen rather than decide, and route to official/trusted assisters.

### P1 — Launch two distribution pilots and certified Spanish QA

- **What:** one FQHC/211 navigator pilot and one employer/union/credit-union pilot; certify core Spanish policy/application language and test accessibility. Sponsors receive aggregate metrics only.
- **Why/evidence:** HRSA reports 1,400 health centers, 16,600 sites, 32.7M patients, with about 90% of patients ≤200% FPL; 211 reports 99% U.S. population coverage. Sources: HRSA current 2025–26 pages and 211 current impact page, accessed Nov. 22, 2026: <https://bphc.hrsa.gov/about-health-center-program>, <https://data.hrsa.gov/topics/health-centers/>, <https://211.org/about-us/our-impact/>.
- **Effort:** M.
- **Dependencies:** agreements, training, referral SLAs, language/accessibility experts, independent feedback.
- **Risk/control:** partner surveillance or workflow capture. Prohibit individual case access and partner influence on eligibility; publish conflict policy.

## Next 12 months

### P0 — Reach audited national nonprofit coverage, then expand by legal obligation

- **What:** cover all matched nonprofit facilities with patient-ready records or explicit “not yet verified” status; then add public/for-profit facilities where state law or a published policy creates relevant rights. Publish quarterly coverage, freshness, error, correction, and reviewer-agreement reports.
- **Why/evidence:** Schedule H is limited to tax-exempt filers, while state laws such as Washington and California extend beyond that federal tax category. Sources: IRS Schedule H instructions (2025), Washington RCW 70.170.060, and California HCAI current FAQ; accessed Nov. 22, 2026: <https://www.irs.gov/instructions/i990sh>, <https://app.leg.wa.gov/rcw/default.aspx?cite=70.170.060>, <https://hcai.ca.gov/affordability/hospital-fair-billing-program/hospital-bill-complaint-program/frequently-asked-questions/>.
- **Effort:** L.
- **Dependencies:** stable national ingest, reviewer operations, correction appeals, state-law coverage.
- **Risk/control:** “national” can conceal poor field coverage. Publish facility- and field-level denominators and staleness; never fabricate missing rules.

### P1 — Release a consent-based caseworker dashboard

- **What:** case queues, evidence packet, delegated access, notes, deadlines, language/accessibility needs, referral status, and outcome verification for trained navigators.
- **Why/evidence:** assisted channels can reach high-need populations through FQHCs and 211; national reach figures are cited above.
- **Effort:** L.
- **Dependencies:** pilot evidence, role-based access, consent/delegation, audit logs, data-retention policy, partner training.
- **Risk/control:** increased breach and UPL exposure. Least privilege, expiring access, no shared accounts, explicit task scope, and escalation protocols.

### P1 — Publish an evidence-first FAP scorecard/compliance checker

- **What:** measure document availability, current dates, stated thresholds, Schedule H consistency, statutory-floor conflicts, application usability, translations, and provider-list availability. Allow hospital responses and corrections; call outputs “document checks,” not final legal findings.
- **Why/evidence:** Lown’s 2026 fair-share project evaluates 3,037 hospitals using FY2023 IRS/CMS/property data, demonstrating demand for public benchmarking. Source: Lown Institute, 2026; accessed Nov. 22, 2026: <https://lownhospitalsindex.org/hospital-fair-share-spending-2026/>.
- **Effort:** L.
- **Dependencies:** mature national dataset, published methodology, governance board, counsel, response process.
- **Risk/control:** false compliance/defamation claims and funder influence. Show evidence, distinguish observations from conclusions, disclose funders, and maintain independent correction review.

### P2 — Evaluate price-transparency evidence, not automated “overcharge” verdicts

- **What:** ingest a limited set of hospital machine-readable rates for common shoppable services and present relevant comparisons as questions/evidence for expert review.
- **Why/evidence:** CMS requires machine-readable standard charges and information for 300 shoppable services, but explicitly warns that displayed prices may not equal a patient’s actual out-of-pocket amount. Sources: CMS, Mar. 2026 fact sheet and June 2026 FAQ; accessed Nov. 22, 2026: <https://www.cms.gov/files/document/mln7215754-hospital-price-transparency.pdf> and <https://www.cms.gov/files/document/hpt-policy-faqs-june-2026.pdf>.
- **Effort:** L.
- **Dependencies:** code/unit/setting matching, payer-plan context, MRF quality controls, domain experts.
- **Risk/control:** false overcharge findings from packaging, modifiers, contracts, or benefit design. Do not automate an accusation or savings estimate.

### P2 — Establish durable funding and independent evaluation

- **What:** combine grants for public infrastructure/evaluation, aggregate-only sponsored distribution, and optional policy-data/API licensing; keep patient access free and prohibit user-data sale. Pre-register an independent study of application completion, approvals, realized savings, collections outcomes, and equity.
- **Why/evidence:** Arnold Ventures reports health-care affordability/evidence grantmaking and funded medical-debt/hospital-market research; RWJF supports and publishes affordability research. Sources: Arnold Ventures, Nov. 16, 2026 and 2025 Form 990-PF; RWJF, Oct. 2, 2026; accessed Nov. 22, 2026: <https://www.arnoldventures.org/stories/our-2025-approach-to-giving>, <https://assets.arnoldventures.org/uploads/LJAF_990-PF_2025-FORM.pdf>, <https://beta.rwjf.org/en/insights/our-research/2026/10/more-than-one-quarter-of-us-adults-had-medical-debt-in-2025.html>.
- **Effort:** L.
- **Dependencies:** nonprofit/governance choice, budget, data-use policy, evaluator, partner cohort.
- **Risk/control:** funder or hospital conflicts and inflated savings claims. Independent board/methodology, funding disclosure, no case-level sponsor data, and separate nominal from realized benefit.

## Explicitly defer

- **Blanket credit-deletion promises:** the 2025 CFPB rule was vacated July 11, 2025, and the remaining federal, bureau, and state rules vary. Sources: *Federal Register*, Jan. 14, 2025; E.D. Tex., July 11, 2025; CFPB guidance reviewed Sept. 5, 2025, accessed Nov. 22, 2026: <https://www.govinfo.gov/content/pkg/FR-2025-01-14/pdf/2024-30824.pdf>, <https://www.govinfo.gov/content/pkg/USCOURTS-txed-4_25-cv-00016/pdf/USCOURTS-txed-4_25-cv-00016-0.pdf>, <https://www.consumerfinance.gov/ask-cfpb/do-medical-bills-affect-my-credit-and-where-do-i-find-out-whats-in-my-medical-payment-history-en-1837/>.
- **An “80% billing-error” marketing claim:** KFF found perceived errors—43% of adults and 53% of adults with health-care debt—not an audited error rate. Source: KFF, July 14, 2022; accessed Nov. 22, 2026: <https://www.kff.org/private-insurance/could-consumer-assistance-be-helpful-to-people-facing-medical-debt/>.
- **Autonomous negotiation or legal advice:** first prove safe facility matching, policy accuracy, application completion, and human escalation. UPL is state-specific; source: American Bar Association, July–August 2024; accessed Nov. 22, 2026: <https://www.americanbar.org/groups/law_practice/resources/law-practice-magazine/2024/july-august-2024/lowering-upl-risk-for-nonlawyer-legal-help/>.

---

# Schedule H as a national policy-discovery backbone

**Bottom line.** Schedule H is feasible as a national *discovery and cross-check layer*, not a complete policy database. It exposes broad free/discount income thresholds and facility-level criteria, but not the full tier ladder, document rules, deadlines, covered providers, application instructions, or live policy. It covers tax-exempt filers and trails current practice. Certainty is **high** on fields/limits and **medium** on automated match yield until multiple filing years are tested.[1]

## What Schedule H can supply

Part I, line 3 reports organization-level free/discount FPG thresholds and other tests. Part V, Section B, line 13 gives facility thresholds and flags income, asset, medical-indigency, insurance, residency, and other criteria; lines 14–20 cover AGB, applications, publicity, collection actions, and reasonable efforts. “000” can mean no FPG test, with another test explained in Part VI, so zero/blank/narrative cases require review.[1]

## Proposed ingestion and matching pipeline

1. **Acquire/version.** Poll IRS monthly index/XML releases; retain return ID, EIN, tax period, submission/object ID, schema, URL, checksum, and amended history.[2][3]
2. **Parse.** Map year-specific tags into a versioned schema; preserve exact XML paths/values; model the filer and every Part V facility separately; never invent missing tiers.
3. **Resolve.** Match CCN first, then scored CMS name/address/ZIP/phone/type/ownership. NPPES can add aliases/locations, but public data suppress EIN/TIN and NPI does not prove ownership.[4][5][6]
4. **Find live documents.** Crawl the official domain for the FAP, summary, application, translations, and provider list required online; store URL, dates, retrieval time, hash, and snapshot.[7]
5. **Extract evidence.** Structure thresholds/tiers, insured treatment, asset/residency, coverage, AGB, deadline, documents, presumptive eligibility, appeals, and collections. Each value points to a text span; validators reject impossible tiers/dates.
6. **Reconcile.** Compare live policy, Schedule H, and state-law floor. Conflicts go to review and remain visible; current procedure comes from the live policy and verified rights from the dated law layer.
7. **Refresh.** Update IRS/CMS monthly, hash-check policies quarterly, and review ownership, broken links, date/threshold changes, or denials. Dollar For’s quarterly checks and two-reviewer reconciliation are a useful benchmark.[8]

## Expected gaps and mitigations

| Gap | Consequence | Mitigation |
|---|---|---|
| Coverage/latency | Nonprofit-only filings can be old; other facilities are absent. | Start from CMS, crawl unmatched facilities, show effective/retrieved dates.[4] |
| Parent vs. facility | One EIN may cover many campuses. | Preserve hierarchy and expose the exact Part V match. |
| Missing policy detail | Thresholds omit tiers, documents, exclusions, and pathways. | Treat Schedule H only as discovery/cross-check. |
| Schema/narrative variation | Tags, “000,” blanks, and prose create false facts. | Version adapters; raw evidence; review zero/narrative cases. |
| Identity churn | Names, owners, domains, and CCNs change. | Version links and CMS ownership; never treat NPI as ownership proof.[4][6] |

## Build-versus-license recommendation

Use a hybrid. HospitalAid’s Nov. 21, 2026 open release provides CCN-linked evidence for 3,496 hospitals under CC BY 4.0; import it as an attributed, independently validated seed.[9] Keep IRS, CMS, and live documents as the reproducible source layer. AHA data can improve matching but are licensed and should remain optional.[10]

## Sources

1. IRS, *2025 Instructions for Schedule H (Form 990)*, 2025; accessed November 22, 2026. <https://www.irs.gov/instructions/i990sh>
2. IRS, *Form 990 Series Downloads*, current 2026 index and XML releases, undated/current page; accessed November 22, 2026. <https://www.irs.gov/charities-non-profits/form-990-series-downloads>
3. IRS, *Tax Exempt Organization Search Bulk Data Downloads*, reviewed May 19, 2026; and *TEOS FAQs*, undated/current page; accessed November 22, 2026. <https://www.irs.gov/charities-non-profits/tax-exempt-organization-search-bulk-data-downloads> and <https://www.irs.gov/charities-non-profits/tax-exempt-organization-search-teos-faqs>
4. CMS, *Hospital General Information*, last modified October 26, 2026 and released November 12, 2026; accessed November 22, 2026. <https://data.cms.gov/provider-data/dataset/xubh-q36u>
5. CMS, *Hospital Data Dictionary*, current data dictionary; publication date not displayed; accessed November 22, 2026. <https://data.cms.gov/provider-data/sites/default/files/data_dictionaries/hospital/HOSPITAL_Data_Dictionary.pdf>
6. CMS, *NPPES Data Dissemination*, monthly file dated November 9, 2026, and CMS readme explaining suppressed SSN/IRS ITIN/EIN; accessed November 22, 2026. <https://download.cms.gov/nppes/NPI_Files.html> and <https://edit.cms.gov/Regulations-and-Guidance/Administrative-Simplification/NationalProvIdentStand/Downloads/Data_Dissemination_File-Readme.pdf>
7. IRS, *Financial Assistance Policy and Emergency Medical Care Policy — Section 501(r)(4)*, undated/current page; accessed November 22, 2026. <https://www.irs.gov/charities-non-profits/financial-assistance-policy-and-emergency-medical-care-policy-section-501r4>
8. McGarry et al., *US Nonprofit Hospitals’ Financial Assistance Policies, 2024*, *Health Affairs Scholar*, November 2024 (PubMed Central version posted 2025); accessed November 22, 2026. <https://pmc.ncbi.nlm.nih.gov/articles/PMC12230784/>
9. HospitalAid, *Open Data*, version published November 21, 2026; accessed November 22, 2026. <https://hospitalaid.org/open-data/>
10. American Hospital Association, *AHA Annual Survey Database*, undated/current product page; accessed November 22, 2026. <https://www.ahadata.com/aha-annual-survey-database>

