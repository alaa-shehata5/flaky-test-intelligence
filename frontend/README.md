# Frontend — Flaky Test Intelligence Dashboard

React + TypeScript + Vite. Typed API client in `src/api/` (no raw `fetch()`
in components); shared loading/error/empty states; sidebar layout with
Dashboard, Tests, Flaky Tests, Runs, and Test Detail pages.

## Setup

```bash
npm install
cp .env.example .env   # VITE_API_URL, default http://localhost:8000
npm run dev            # http://localhost:5173
```

The backend must be running and reachable (CORS allows `localhost:5173`).

## Scripts

```bash
npm run dev            # dev server
npm run build          # typecheck + production build
npm run lint           # eslint
npm run format         # prettier
npm run preview        # serve the production build
```

## Structure

```text
src/
  api/        types, fetch client with error envelope, endpoint functions
  hooks/      useApi data-fetch hook
  components/ Layout (sidebar/header), loading/error/empty states
  pages/      Dashboard, Tests, FlakyTests, Runs, TestDetail
```
