# Demo Script (3–5 minutes)

Audience: a technical reviewer. All data below comes from `flakyctl
seed-demo` (deterministic: 50 runs × 30 tests) — reproduce it with
`docker compose up --build` then `docker compose exec backend flakyctl
seed-demo`.

## 1. The problem (30s)

"CI tells us each run passed or failed. It doesn't tell us *which tests
can't be trusted*. One flaky payment test can block every release train."

## 2. Seed history (30s)

```bash
flakyctl seed-demo
# seeded 50 runs x 30 tests for project 'demo-project'
```

## 3. Evaluate the detector (45s)

```bash
flakyctl analyze
# eval: TP=9 TN=21 FP=0 FN=0 precision=1.000 recall=1.000
```

"Nine genuinely flaky tests found, zero false alarms — against labels the
scorer never sees."

## 4. Open the dashboard (60s)

Open `http://localhost:3000`. Point at the KPI cards (30 tests, 9 flaky,
2 newly flaky), then the severity chart and the pass-rate trend.

## 5. Triage one test (90s)

Open **Flaky Tests**, sort by score, open `test_session_refresh` (50/50
pass/fail, score ≈ 82). Show: classification HIGHLY_FLAKY, the flat
score history, alternating execution strip. Then open
`test_checkout_coupon`: overall score only ≈ 30 (MOSTLY_STABLE) but flagged
**newly flaky** — stable for 35 runs, then failing. "This is the one to
fix before it becomes chronic."

## 6. Close (30s)

"Upload any JUnit XML to `POST /api/runs/upload` and history starts
accumulating. Docs: `docs/detection-algorithm.md` for the math,
`docs/api.md` for integration."
