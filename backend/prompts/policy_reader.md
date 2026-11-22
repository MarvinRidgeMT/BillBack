You are extracting rules from a U.S. nonprofit hospital's Financial Assistance Policy (FAP), also called a charity care policy. Your output is read by software that decides whether a low-income patient likely qualifies, so accuracy matters more than completeness. A wrong number is worse than a null.

The policy text follows, split into pages marked "=== PAGE n ===". Tables appear under "[TABLES]" as pipe-delimited rows. If a PDF is attached, it is the same policy; use it for pages marked as having no text layer.

Extract these fields into the provided JSON schema:
1. free_care.fpl_max_percent: the highest household income, as a percent of the Federal Poverty Level (FPL/FPG), at which care is 100% free (a 100% discount, or "no charge").
2. discount.fpl_max_percent: the highest income (% FPL) that gets any discount at all, including "pays Amount Generally Billed (AGB)" discounts.
3. discount.tiers: each discount band above the free-care limit, in increasing order: its FPL range and what the patient gets. Keep the policy's own boundaries exactly ("201% to 300%" means min 201, max 300; "up to and including 400%" means max 400). Use discount_type:
   - percent_off: patient gets X% off charges (value = X)
   - pays_percent_of_charges: patient pays X% of charges (value = X)
   - amount_generally_billed: patient pays no more than AGB (value = null)
   - sliding_scale: a scale is mentioned but no fixed number applies (value = null)
   - other: anything else; explain in description
   Do not include the free-care band as a tier.
4. asset_test: whether assets (savings, property, investments, retirement accounts) are considered, and how. applies=false only if the policy says assets are NOT considered.
5. residency: whether patients must live in a specific state, county, or service area, and which. required=false only if the policy says residency is not required.
6. application_window: how many days a patient has to apply, and what the clock starts from. Use the application deadline, not the collections (extraordinary collection action) notice period, unless they are the same.

Also fill: hospital_name (the hospital or health system that issued the policy), hospital_state, policy_effective_date (as written), income_basis, uses_income_table, insured_patients_eligible, presumptive_eligibility (one short sentence), how_to_apply (address, phone or portal as written), and warnings.

Evidence rules:
- Every one of the 6 fields needs evidence: copy the exact sentence(s) from the policy text, verbatim, character for character, under 60 words, and give the page number it appears on. Do not paraphrase, merge sentences from different places, fix typos, or add words. For a table row, copy the row text as it appears.
- If the policy does not state something, set the value(s) to null (where the schema has no null: "" for text, 0 for a number of days), quote to "", page to 0, and confidence 0.0-0.3. Never guess or fill in typical values (do not assume 200%/400% FPL or 240 days because they are common).
- confidence: 0.9-1.0 = stated explicitly in one place; 0.6-0.89 = needed light interpretation (for example combining a table header with a row); below 0.6 = unclear or inferred.

Interpretation rules:
- "Federal Poverty Guidelines", "FPG", "FPL", "Federal Poverty Income Guidelines" and "poverty level" all mean the same thing.
- If thresholds are given as a dollar income table rather than % of FPL, set uses_income_table=true. Fill fpl_max_percent only if the policy explicitly states the % of FPL the table is based on; otherwise leave it null and add a warning.
- If several hospitals or facilities are covered, extract the rules for the hospital or system named in the title, and add a warning naming the others if their rules differ.
- If the policy contradicts itself, use the more specific statement (the table over the summary) and add a warning describing the conflict.
- Report thresholds only. Do not decide anyone's eligibility, do not calculate incomes, and do not add advice.
