# Automated cross-check: AI-written key vs. the policy reader (not accuracy)

**What this is:** B's `answer_key.json` (branch `person-b-eligibility`, commit `264b386`) for 6 real policies
(Adena, Baptist Memorial, Boys Town, Fort HealthCare, Marshfield, USA Health). **It was written by an AI (Claude Code), not
checked by a person** (confirmed by the team, Nov 22 12:25pm). So agreement here is our AI agreeing with an AI, and we do
**not** report it as accuracy.

**Result:** the reader agrees with that key on **35 of 36** values (6 policies × free care, discount, asset test, residency,
application window, source URL). On the six benchmark fields (free-care limit, discount limit, discount tiers, asset test,
residency, application window) it is also 35/36. The one disagreement: Marshfield's application window starts at the
"first billing statement" in the key and "other" in the reader.

Why it isn't independent: the key matches the reader's cached output on 30/30 page numbers, 20/30 confidence values and
20/30 quotes character for character.

Reproduce (no AI calls): `.venv/bin/python eval/cross_check/b_score_policies.py` → `b_scoring_results.json`.
Files are B's, copied unchanged except the three file paths (so the script runs from any folder).

The accuracy benchmark needs answers a **person** verified from each PDF: see `eval/verify/`.
