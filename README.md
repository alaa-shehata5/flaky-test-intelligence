# Flaky Test Intelligence Platform

Collects JUnit test results across CI runs, stores execution history in
PostgreSQL, scores test instability with a statistical engine, and presents
QA intelligence in a React dashboard.

> Status: Phase 0–2 in progress (backend foundation + data model).
> See `docs/requirements.md` for scope and `implementaion_plan.md` for the
> phased build plan.

## Quick start (current phase)

```bash
# backend (once Phase 1 lands)
python -m venv .venv && source .venv/bin/activate
pip install -e "backend[dev]"
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload --app-dir backend
curl localhost:8000/health
```

Full one-command startup (`docker compose up --build`) lands in Phase 10.

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
