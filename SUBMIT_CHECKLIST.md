# Submit checklist (Anish, 1:45 → 2:15pm ET; hard deadline 3:00pm ET)

Go top to bottom. Tick each box only after you've seen it work.

## Repo
- [ ] Replace `TODO_NAME` (team names / GitHub handles) in `README.md` and `DEVPOST.md`.
- [ ] Replace `TODO_VIDEO_URL` and `TODO_DEMO_URL` in `README.md` and `DEVPOST.md` (no deployed demo? change the demo line to "Run locally: see README").
- [ ] Commit and push: `git add README.md DEVPOST.md && git commit -m "docs: final links and team names" && git push origin main`
- [ ] Make the repo public: GitHub → MarvinRidgeMT/BillBack → Settings → General → Danger Zone → Change visibility → Public. (Security pass is done: no keys in history, `.env` never committed, no real patient data, MIT license.)
- [ ] Open https://github.com/MarvinRidgeMT/BillBack in an incognito window: the README renders, the Mermaid diagram shows, and the numbers match the video.
- [ ] Tag it: `git tag -a v1.0-submission -m "EvoHacks II submission" && git push origin v1.0-submission`
- [ ] Optional: delete the old personal copy (AniMeruva-cmyk/BillBack → Settings → Delete).

## Demo
- [ ] Either the demo link opens logged out, or the README's "Run it locally" steps work. (They were tested from a fresh clone at 11:17am: 215 tests passed, the demo-mode backend answered, and the front end built.)

## Video
- [ ] Under 3:00.
- [ ] Uploaded as **Public** (not Unlisted/Private) on YouTube or Vimeo; opens in an incognito window.
- [ ] Says only the numbers in NOTES_FOR_TEAM.md → "FINAL NUMBERS FOR VIDEO".

## Devpost form (copy from DEVPOST.md)
- [ ] Name, tagline, every description section
- [ ] Video URL, repo URL, demo URL (or "run locally")
- [ ] Built-with tags
- [ ] "Built during the event" statement
- [ ] All 3 team members added to the project on Devpost
- [ ] **Click Submit by 2:15pm ET** (deadline 3:00pm ET), then reload the page and check it shows as submitted
