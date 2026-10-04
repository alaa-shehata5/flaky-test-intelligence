# Data Model

Four tables store the full history. All timestamps are timezone-aware.

## Tables

### `projects`

| Column | Type | Notes |
|---|---|---|
| id | integer PK | autoincrement |
| name | varchar(255), unique, not null | human + API identifier |
| repository | varchar(1024), nullable | informational |
| created_at | timestamptz, not null | |

### `test_runs`

One ingested CI run. Unique per `(project_id, run_number)` so re-uploads
are rejected instead of double-counted.

| Column | Type | Notes |
|---|---|---|
| id | integer PK | |
| project_id | FK → projects.id, cascade delete | indexed (branch + created composites) |
| run_number | integer, not null | CI run number |
| commit_sha | varchar(64), nullable | |
| branch | varchar(255), not null, default `main` | indexed |
| workflow_name / environment | varchar(255), nullable | filter dimensions |
| started_at / finished_at | timestamptz, nullable | |
| total/passed/failed/skipped/error_tests | integer, not null | denormalized counters |
| total_duration | float, not null | seconds, summed at ingest |
| source | varchar(64), default `junit` | future formats |
| created_at | timestamptz, indexed | |

### `test_cases`

One logical test, stable across runs.

| Column | Type | Notes |
|---|---|---|
| id | integer PK | |
| project_id | FK → projects.id, cascade delete | |
| suite_name | varchar(255), nullable | |
| classname / test_name | varchar(1024), not null | |
| unique_key | varchar(2048), unique, not null | **test identity** (below) |
| first_seen_at / last_seen_at | timestamptz, not null | observability |

### `test_executions`

One test outcome inside one run.

| Column | Type | Notes |
|---|---|---|
| id | integer PK | |
| run_id | FK → test_runs.id, cascade delete | indexed |
| test_case_id | FK → test_cases.id, cascade delete | indexed, incl. `(test_case_id, executed_at)` composite |
| status | varchar(16), CHECK in `passed/failed/error/skipped` | |
| duration | float, not null | seconds |
| failure_message | text, nullable | truncated at 4000 chars on ingest |
| failure_type | varchar(255), nullable | |
| executed_at | timestamptz, indexed | chronological ordering |

## Relationships

```text
Project 1──* TestRun 1──* TestExecution *──1 TestCase *──1 Project
```

Deleting a project cascades to its runs, cases, and executions (tested).

## Test identity

A logical test is `project::classname::test_name`, e.g.
`demo-project::tests.test_auth::test_valid_login`, stored in
`test_cases.unique_key` (unique index). Same test across runs → same key;
different tests → different keys. A second uniqueness guard on
`(project_id, classname, test_name)` prevents the same logical test from
being stored under two different keys. Duplicate records inside one JUnit
file are collapsed when identical and rejected with
`CONFLICTING_TEST_RECORDS` when they disagree.

## Indexes

- Unique: `test_cases.unique_key`, `(project_id, run_number)`,
  `(project_id, classname, test_name)`
- Foreign keys: `test_executions(run_id)`, `test_executions(test_case_id)`
- History queries: `(test_case_id, executed_at)`, `executed_at`
- Dashboard filters: `(project_id, branch)`, `(project_id, created_at)`,
  `(project_id, classname, test_name)`, `test_runs.created_at`,
  `test_cases.last_seen_at`

## Migrations

Alembic, linear history (`alembic upgrade head` / `downgrade base` both
verified on PostgreSQL 16 and SQLite). Batch mode keeps SQLite compatible.
