# API Reference

Base URL: `http://localhost:8000`. Interactive docs: `/docs`.
Errors always look like:

```json
{ "error": "TEST_NOT_FOUND", "message": "test 9 not found", "request_id": "abc123" }
```

Conventions: `limit` (1–200, default 50), `offset` (default 0);
`project_id`, `branch`, `workflow_name`, `environment`, `date_from`,
`date_to` scope runs/executions; `classification` is one of
`INSUFFICIENT_DATA STABLE MOSTLY_STABLE SUSPECTED_FLAKY HIGHLY_FLAKY
CONSISTENTLY_FAILING`.

## Projects

```bash
POST /api/projects                      # {"name": "shop", "repository": "..."} → 201
GET  /api/projects                      # items + run/test counts
GET  /api/projects/1
```

## Runs

```bash
GET  /api/runs?project_id=1&branch=main&limit=20
GET  /api/runs/51

# Ingest JUnit (multipart):
curl -X POST localhost:8000/api/runs/upload \
  -F file=@results.xml -F project=shop -F run_number=52 -F branch=main
# → 201 {"run_id": 52, "summary": {"total": 5, "passed": 2, ...}}
# Errors: INVALID_FILE_TYPE (400), INVALID_JUNIT_FILE (400),
#         FILE_TOO_LARGE (413, 5 MB), DUPLICATE_RUN (409),
#         CONFLICTING_TEST_RECORDS (400)
```

## Tests

```bash
GET /api/tests?project_id=1&classification=HIGHLY_FLAKY&minimum_score=70&q=payment
GET /api/tests/23        # full analysis: rates, durations, score, trends, flags
GET /api/tests/23/history
# [{"run_number": 1, "status": "passed", "duration": 0.9,
#   "executed_at": "...", "score": 0.0, "failure_message": null, ...}]
```

## Flaky tests (ranked)

```bash
GET /api/flaky-tests?project_id=1&sort=score_desc&limit=20
# sort: score_desc|score_asc|pass_rate_asc|pass_rate_desc|name_asc
# Newly-flaky tests are included even below minimum_score (their recent
# window already classified flaky at threshold).
```

## Dashboard

```bash
GET /api/dashboard/summary?project_id=1&branch=main
# {"total_tests": 30, "total_runs": 50, "stable_tests": 17,
#  "suspected_flaky_tests": 5, "highly_flaky_tests": 2,
#  "consistently_failing_tests": 3, "slow_tests": 2,
#  "newly_flaky_tests": 2, "average_pass_rate": 0.8033}
```
