# BillBack front end

Next.js (App Router) + Tailwind + shadcn/ui + Motion. Design: `../docs/superpowers/specs/2026-11-22-frontend-design.md`.

## Run it

Two terminals.

```bash
# 1. backend, from the repo root (needs .env with the API key)
.venv/bin/uvicorn backend.app:app --reload

# 2. front end
cd frontend
cp .env.example .env.local   # first time only
npm install                  # first time only
npm run dev                  # http://localhost:3000
```

The browser only talks to Next.js. `next.config.ts` proxies `/api/*` to `BACKEND_URL`
(default `http://localhost:8000`), so the backend needs no CORS setup.

## Notes

- Nothing is stored. The bill and the answers live in React state and are gone on refresh.
- No secrets here. Never put an API key in this folder.
- `NEXT_PUBLIC_DEMO_MODE=1` lets the app offer a clearly labeled sample when the backend
  can't answer. A sample is never shown as a real result.
- All user-facing strings are in `messages/en.json`. `messages/es.json` has the same keys
  and still holds English placeholders.
- `npm run build` must pass before a commit.
