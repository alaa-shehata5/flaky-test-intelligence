# Flaky Test Intelligence Platform

Collects JUnit test results across CI runs, stores execution history in
PostgreSQL, scores test instability with a statistical engine, and presents
QA intelligence in a React dashboard.

> Status: Phase 0–2 in progress (backend foundation + data model).
> See `docs/requirements.md` for scope and `implementaion_plan.md` for the
> phased build plan.

## Quick start (current phase)

```bash
# from the repository root
python -m venv .venv && source .venv/bin/activate
python -m pip install -e "backend[dev]"
cp .env.example .env
alembic -c backend/alembic.ini upgrade head
uvicorn app.main:app --reload --app-dir backend
curl localhost:8000/health
```

## Run everything (Docker)

```bash
docker compose up --build
```

Then open:

- Dashboard: http://localhost:3000
- API: http://localhost:8000/docs
- Health: http://localhost:8000/health

Seed demo data once the backend is up:

```bash
docker compose exec backend flakyctl seed-demo
```

Ports and credentials are overridable via a local `.env` file; see
`.env.example`. The backend container applies Alembic migrations on startup
and refuses to serve if they fail.

## Run in Codespaces

```text
Open repository
  ↓
Create Codespace (Code → Codespaces → Create codespace on main)
  ↓
docker compose up --build
  ↓
open dashboard (forwarded port 3000)
```

The dev container ships Python 3.12, Node 24, and Docker-in-Docker, and
forwards ports `3000` (dashboard), `8000` (API/Swagger), `5173` (Vite dev)
and `5432` (Postgres). For local frontend development instead of the
prebuilt image:

```bash
npm --prefix frontend install
npm --prefix frontend run dev   # http://localhost:5173
```

## CLI (`flakyctl`)

```bash
flakyctl seed-demo                                   # 50 deterministic CI runs x 30 tests
flakyctl ingest demo/sample-results.xml --project demo-project --run-number 51
flakyctl analyze                                     # classifications + precision/recall
flakyctl list-flaky --min-score 40 --limit 20
```

## Project structure

```text
backend/    FastAPI + SQLAlchemy + Alembic
frontend/   React + TypeScript + Vite (Phase 7+)
cli/        flakyctl entry points (Phase 5+)
demo/       deterministic synthetic data (Phase 5+)
docs/       requirements, architecture, data model, detection algorithm
scripts/    helper scripts
tests/      root-level placeholders (backend tests live in backend/tests)
.github/    CI workflows (Phase 12)
.devcontainer/  Codespaces config (Phase 11)
```

## Docs

- `docs/requirements.md` — problem, users, FR/NFR, MVP vs future scope
- `docs/architecture.md` — system design (skeleton, completed in Phase 14)
- `docs/data-model.md` — tables, identity, indexes (skeleton)
- `docs/detection-algorithm.md` — scoring pipeline (skeleton, completed in Phase 4)

## Development rules

- One phase / one task at a time; verify before moving on.
- No fabricated test results, screenshots, or metrics.
- Synthetic demo data is always labeled as such.
- Never commit secrets (`.env` is gitignored; `.env.example` documents vars).
