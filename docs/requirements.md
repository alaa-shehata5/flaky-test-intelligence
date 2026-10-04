# Requirements — Flaky Test Intelligence Platform

## 1. Problem Statement

CI test suites grow large and historical results are scattered across individual
CI runs (JUnit XML artifacts, workflow logs). Teams cannot easily answer:

- Which tests are flaky vs. consistently broken vs. stable?
- Is a test getting worse over time?
- Which flaky tests should be quarantined or fixed first?
- Did a recent change introduce new instability?

Existing CI UIs show per-run pass/fail but lack cross-run intelligence,
trend analysis, and flakiness scoring. This platform ingests JUnit results
over time, stores normalized execution history in PostgreSQL, computes
statistical flakiness signals, and exposes them via API + dashboard.

## 2. Target Users

- **QA Engineers / SDETs**: triage flaky tests, prioritize fixes, track reliability.
- **Backend / Frontend developers**: check whether a failure they see is a known flake.
- **DevOps / Test-infra engineers**: monitor suite health, slow tests, CI stability.
- **Engineering managers / portfolio reviewers**: assess product quality practices.

## 3. Functional Requirements

| ID | Requirement | Maps to Phase |
|----|-------------|---------------|
| FR-1 | Ingest JUnit XML for a project/run (project, branch, commit, run_number, workflow, environment) via `POST /api/runs/upload` | Phase 3, 6 |
| FR-2 | Secure XML parsing: handle suites/cases/classname/duration/failures/errors/skipped; reject malformed XML, XXE, entity expansion with useful errors | Phase 3, 13 |
| FR-3 | Deterministic test identity `project::classname::test_name` stable across runs; duplicates handled safely | Phase 3 |
| FR-4 | Persist projects, test runs, test cases, test executions in PostgreSQL with Alembic migrations | Phase 2 |
| FR-5 | Compute per-test statistics: sample size, pass/fail/error/skip counts, pass & failure rates | Phase 4 |
| FR-6 | Compute duration stats: min/max/mean/median/p95/stddev | Phase 4 |
| FR-7 | Compute outcome inconsistency, recency-weighted failure signal, duration instability, composite 0–100 flakiness score (configurable weights/thresholds) | Phase 4 |
| FR-8 | Classify tests: INSUFFICIENT_DATA, STABLE, MOSTLY_STABLE, SUSPECTED_FLAKY, HIGHLY_FLAKY, CONSISTENTLY_FAILING; detect newly-flaky and persistently-flaky | Phase 4 |
| FR-9 | Trend analysis: pass-rate, failure-rate, duration, score trends over runs | Phase 4 |
| FR-10 | REST API: projects, runs (paginated + upload), tests (filtered), flaky-tests (sorted/paginated), test history, dashboard summary; consistent error envelope | Phase 6 |
| FR-11 | Dashboard: KPI cards, flaky-test table (search/filter/sort/paginate), outcome & severity charts, pass-rate & duration trends, test detail + execution history + failure messages, global filters | Phase 7, 8 |
| FR-12 | Deterministic synthetic demo data: 30–100 runs, 20–50 tests covering stable/flaky/broken/slow/skipped/insufficient-history; `flakyctl seed-demo`, `ingest`, `analyze`, `list-flaky`; ground-truth labels + precision/recall evaluation (labels never used for scoring) | Phase 5 |
| FR-13 | Docker Compose one-command startup (postgres + backend + frontend); Codespaces devcontainer; GitHub Actions CI (backend lint/test/coverage, frontend lint/test/build, Docker build, JUnit artifact) | Phase 10, 11, 12 |
| FR-14 | Hardening: upload type/size limits, CORS from env, no stack-trace/secret leakage, dependency review | Phase 13 |
| FR-15 | Portfolio documentation: README, architecture (with diagram), data model, detection algorithm, API docs, demo script, portfolio summary; real evidence only (no fabricated screenshots/metrics) | Phase 14, 15 |

## 4. Non-Functional Requirements

- **NFR-1 Performance**: p95 dashboard summary < 1s on demo dataset (30–100 runs × 20–50 tests) on a laptop.
- **NFR-2 Reliability**: ingestion is idempotent-safe at the run level; duplicate JUnit records do not corrupt history.
- **NFR-3 Maintainability**: simple layered architecture (API → service → DB), typed code (Pydantic, TypeScript), Ruff + ESLint/Prettier clean.
- **NFR-4 Testability**: pytest coverage for models, parser, analysis, API; frontend component + error-state tests; `npm run build` passes.
- **NFR-5 Portability**: `docker compose up --build` works on a clean machine; Codespaces works without manual fixes.
- **NFR-6 Security**: no secrets in git, `.env` never committed, XXE-safe XML, CORS allowlist, upload size caps.
- **NFR-7 Observability**: structured logs (timestamp, level, logger, request_id); health endpoint; consistent API error envelope with `request_id`.
- **NFR-8 Honesty**: synthetic demo data clearly labeled; no fabricated test results, screenshots, or metrics.

## 5. Major Features (MVP)

1. JUnit ingestion → PostgreSQL history.
2. Statistical analysis engine + classification.
3. REST API for all dashboard needs.
4. React dashboard with KPIs, tables, charts, test detail.
5. Deterministic demo seeding + CLI.
6. Docker + CI + docs.

## 6. Constraints

- Input format MVP: JUnit XML only.
- Single database: PostgreSQL (SQLite allowed only for unit tests / local fallback).
- Python 3.12+, FastAPI + SQLAlchemy + Alembic (per plan).
- Frontend: React + TypeScript + Vite.
- No auth/multi-tenancy in MVP (single-tenant local platform).

## 7. MVP Scope

Phases 0–14 as defined in `implementaion_plan.md`, verified by phase gates.
Phase 15 (real evidence) and 16 (QA audit) must use actual runs, not placeholders.

## 8. Future Scope (out of MVP)

- Additional formats (TestNG, xUnit JSON, Playwright JSON).
- GitHub Checks / PR comments ("this failure looks like known flake #…").
- Test quarantine suggestions + auto-filed issues.
- Authentication, teams, RBAC.
- Real-time ingestion via webhooks.
- ML-based failure clustering (failure-message embeddings).
- Notifications (Slack) for newly-flaky tests.
