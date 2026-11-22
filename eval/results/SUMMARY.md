# Results summary

Every number below comes from a script in `eval/` (run `python -m eval.summary` to rebuild). Bills and households are fictional.

| Test | Measured | Target | Result |
|---|---|---|---|
| Bill extraction (10 fake bills × 5 fields) | 50/50 (100%) | ≥ 90% | ✅ met |
| Policy reader, hand spot-checks (2 real policies × 6 fields) | 11/12 (Boys Town 6/6, USA Health 5/6) | ≥ 90% | ✅ met (small sample, checked by hand) |
| Policy reader, B's hand-checked key (6 real policies × 6 fields) | not measured yet (waiting for B to fill eval/answer_key_real_TODO.csv) | ≥ 90% | — pending |
| Policy quotes verified verbatim in the PDF | 21/21 | all | ✅ met |
| Policy re-run agreement (6 policies × 5 values) | 29/30 | — | info |
| End-to-end households, status (10 households × 20 policies, 2026 FPL) | 10/10 households (200/200 results) | 10/10 | ✅ met |
| …same, every detail incl. unresolved-rule notes | 7/10 households (193/200) | — | info (B to confirm 7 notes) |
| Rules-engine + backend tests | 223 passed, 0 failed, 2 skipped | all pass | ✅ met |
| Speed, bill → result (cached policy) | avg 2.6 s, max 3.3 s | < 60 s | ✅ met |
| Speed, first bill for a new hospital (live policy read) | avg 10.9 s | < 60 s | ✅ met |
| Cost per bill (cached policy) | $0.0096 | < $0.05 | ✅ met |
| Cost, first bill for a new hospital | $0.0528 | < $0.05 | ❌ not met |
| Bill fields sent to the patient to confirm | 2/50 (under 0.8 confidence: 2) | — | info |
| Policy fields sent to human review | 4/30 | — | info |

**Boundary tests:** exactly 200% (household 2, $43,280): pass; $1 over 200%: pass; household of 1 / of 9+ (add-on), AK, HI: pass; missing income rejected: pass; FPL year is 2026 (regression): pass.

In plain words: BillBack read all 50 fields correctly on our 10 fake bills, including crumpled and dim photos, in about 3 seconds and about one cent per bill. The rules engine gave the expected answer for all 10 test households, using the real 2026 poverty guidelines. We could not measure the policy reader against a full hand-labeled answer key; we checked two policies by hand (11 of 12 fields right), and every policy quote we show was found word for word in the hospital's PDF.
