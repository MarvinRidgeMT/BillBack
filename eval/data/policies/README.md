# Policy eval data

Nothing is copied here, so there is one source of truth for each file:

| What | Where |
|---|---|
| The real hospital policy PDFs (B's list + the original six) | `data/policies/*.pdf`, sources and download dates in `data/policies/sources.csv` |
| What the policy reader extracted from them (cached rules JSON, with quote + page + confidence per field) | `cache/policies/*.json` |
| **Answer key**: 6 fields per policy (free-care limit %FPL, discount limit %FPL, discount amount, asset test, residency rule, application window) | `eval/verify/answer_key.csv` (102 rows for the 17 readable policies; `correct_value`, `is_correct`, `verified_by` are filled in by a person using `eval/verify/index.html`) |

`eval/run_all.py` scores **only rows a person marked** (`is_correct` = yes/no and `verified_by` filled in). Until rows are verified
it reports the policy-reader accuracy as pending. The key is never filled from model output.

TODO(team, B): verify the 102 rows in `eval/verify/answer_key.csv` (about 20 seconds each, see `eval/verify/README.md`),
plus the 3 policies that couldn't be downloaded if you can get their PDFs by hand, to reach 120 fields (20 × 6).
