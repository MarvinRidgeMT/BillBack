# Sample bills (fake) — Person C

10 made-up hospital bills for the bill-extraction eval (10 bills × 5 fields = 50).
Every patient name, account number and street address is fictional; each page says SAMPLE in the footer.
Hospital names are the 6 hospitals with cached policies, so the end-to-end flow can match them.

| Condition | Files |
| --- | --- |
| clean photo | bill_01 |
| text PDF | bill_02, bill_09 |
| angled on a table | bill_03, bill_04 (+ slight blur) |
| crumpled | bill_05, bill_06 |
| dim light | bill_07, bill_08 (+ angled) |
| crumpled + dim (hardest) | bill_10 |

`answer_key.csv` has the true values for each bill: hospital_name, hospital_address, amount_due (and cents),
service_date (ISO), account_number, plus hospital_slug and state for the eligibility step.

These are generated images, not real phone photos. If there's time, print 2–3 and photograph them
(add as bill_11+ with rows in answer_key.csv) so the eval includes real camera shots.

Regenerate: `.venv/bin/python sample_bills/make_sample_bills.py` (needs pillow, numpy, scipy, reportlab).
