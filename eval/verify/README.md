# Verification pack: the rest of the 20-policy benchmark

The full benchmark is 20 real policies × 6 fields. B hand-verified 6 policies (`eval/answer_key_real_TODO.csv`).
This pack covers the other 14 so a person can verify them quickly. **Nothing here is filled in by AI**: the answers
must come from a person reading the hospital's PDF, because our AI re-reading the PDF would not be independent of our AI reader.

| | policies | fields |
|---|---|---|
| Not scored by B | 14 | 84 |
| Policy PDF not reachable (left out of the denominator) | 3: HOSP-R001 Adventist Health (site returns 403 to downloads), HOSP-R015 Mission Health (policy is a web page, no PDF), HOSP-R020 Ascension MI (policy moved) | 18 |
| **In this pack** | **11** | **66** |

All three were retried once at 11:40am (one search on the official site for the current PDF); see `eval/results/b_real_policies.md`.

## How to verify (about 20 seconds a field)
1. Open `eval/verify/index.html` in a browser (double-click it; no server needed).
2. Type your name at the top.
3. For each card: read the reader's value, its quote, and the page text around the keywords
   (free, 100%, poverty, FPL, discount, asset, resident, days, apply). Open the PDF if the snippet isn't enough.
4. Click **Reader is right**, or type the correct value and click **Reader is wrong**. Progress is saved in your browser.
5. Click **Export CSV** and save it over `eval/verify/answer_key_14.csv`.
6. Score it (counts only rows with `verified_by` filled in):
   ```
   .venv/bin/python -m eval.policy_benchmark eval/verify/answer_key_14.csv --require-verifier --out eval/results/policy_benchmark_verified.md
   ```

LA County, Mercy and Ochsner PDFs aren't saved in the repo; their cards link to the hospital's PDF instead of a local page.

## Files
- `answer_key_14.csv`: one row per field. `correct_value`, `is_correct`, `verified_by` are BLANK.
- `rows.js`: the same rows for `index.html`.
- Rebuild both from the cached reader outputs (no AI calls): `.venv/bin/python -m eval.verify_pack`.

## Field meanings
- **free_care %**: highest income (% of the federal poverty line) that gets 100% free care.
- **discount max %**: highest income that gets any discount.
- **discount tiers**: the discount bands, e.g. `200-300%: percent 75`.
- **asset test**: does the policy count savings/property? `True`, `False`, or `None` (policy doesn't say).
- **residency**: must the patient live in an area? `None` = policy doesn't say.
- **application window**: days to apply and the day the count starts.

"Not stated" convention: a field the policy doesn't address is `None` in the reader's value. If the policy is silent and the
reader says `None`, mark it right. (Same convention as `backend/eval_config.py`, `NOT_STATED_ANSWER_KEY_VALUE = None`.)
