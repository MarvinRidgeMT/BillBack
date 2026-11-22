# Submit checklist (Anish, by 2:15pm ET; hard deadline 3:00pm ET)

Go top to bottom. Tick each box only after you've seen it work. Claude Code did not change repo visibility, deploy, post or submit.

## Already done (A + Claude Code, 12:15–12:40pm)
- [x] Demo checked at 1440×900 and 390×844, English and Spanish; tagged `demo-freeze` (pushed).
- [x] 263 tests pass, 0 failed (2 skipped: live API). `npm run build` clean.
- [x] Security pass: no API keys anywhere in git history, `.env` never committed, no files over 10 MB, no `.venv`/`node_modules`/`.next`,
      no voice files (browser voice only, so MIT holds), only fictional bills and households.
- [x] Every number in README/DEVPOST/NOTES matches `eval/results/SUMMARY.md`. No "/120" accuracy claim anywhere.
- [x] Policy reader: 11/12 on 2 hand-checked policies. B's six-policy key was AI-written, so it's a cross-check (35/36), not accuracy.
- [x] Old worktrees removed (`../BillBack-wow`, `.claude/worktrees/push-to-git-534df6`). `person-b-eligibility` and `frontend-ui` kept on GitHub.
- [x] `v1.0-submission` tag created **locally** (not pushed).

## Repo (you)
- [x] Team credits filled from the GitHub org (A @AniMeruva-cmyk, B @abhinavmedisetty, C @SiddharthTumati). Add B's full name if B wants it shown.
- [ ] Replace `TODO_VIDEO_URL` and `TODO_DEMO_URL` in `README.md` and `DEVPOST.md` once C uploads
      (no deployed demo? change the demo line to "Run locally: see README").
- [ ] Commit and push: `git add README.md DEVPOST.md && git commit -m "docs: final video and demo links" && git push origin main`
- [ ] Move the tag to that commit and push it: `git tag -f v1.0-submission && git push origin v1.0-submission`
- [ ] Make the repo public: GitHub → MarvinRidgeMT/BillBack → Settings → General → Danger Zone → Change visibility → Public.
- [ ] Open https://github.com/MarvinRidgeMT/BillBack in an incognito (logged-out) window: the README renders, the Mermaid diagram shows,
      the demo/video links open, and the numbers match the video.
- [ ] Optional: delete the old personal copy (AniMeruva-cmyk/BillBack → Settings → Delete).

## Demo
- [ ] Either the demo link opens logged out, or the README's "Run it locally" steps work
      (tested from a fresh clone at 11:17am; tests re-run at 12:27pm: 263 passed).

## Video (C)
- [ ] Under 3:00.
- [ ] Uploaded as **Public** (not Unlisted/Private) on YouTube or Vimeo; opens in an incognito window.
- [ ] Says only the numbers in NOTES_FOR_TEAM.md → "FOR C — RECORDING" / "FINAL NUMBERS FOR VIDEO".
      Policy reader = "we checked two policies by hand: 11 of 12 fields right". Don't say 35/36 or "120 fields" as accuracy.

## Devpost form (copy from DEVPOST.md)
- [ ] Name, tagline, every description section
- [ ] Video URL, repo URL, demo URL (or "run locally")
- [ ] Built-with tags
- [ ] "Built during the event" statement
- [ ] All 3 team members added to the project on Devpost
- [ ] **Click Submit by 2:15pm ET** (deadline 3:00pm ET), then reload the page and check it shows as submitted
