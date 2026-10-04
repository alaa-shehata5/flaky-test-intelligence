# Detection Algorithm

How raw executions become classified QA intelligence.

```text
raw executions
  ↓
statistics (sample, rates, durations)
  ↓
outcome inconsistency (70%)
  ↓  (+) failure recency, exponential decay (15%)
  ↓  (+) duration instability, CV-based (15%)
flakiness score (0–100)
  ↓
classification (+ newly/persistently-flaky flags, trends)
```

## 1. Statistics

For each test, over its ordered execution history (`executed_at`, `id`):

- `sample_size` = number of **non-skipped** executions. Skipped results carry
  no pass/fail signal; they are counted separately (`skipped`) and excluded
  from all rates and scores.
- `pass_rate = passed / sample_size`
- `failure_rate = (failed + error) / sample_size`
- Duration statistics over non-skipped executions: min, max, mean, median,
  p95 (nearest-rank), standard deviation (population, `pstdev`).

## 2. Outcome inconsistency (weight 70%)

```text
inconsistency = 1 - abs(pass_rate - 0.5) * 2        # range 0..1
```

0 for unanimous histories (all pass or all fail), 1 for exactly 50/50.
This is the primary signal: flakiness *is* outcome disagreement. A test that
fails every time scores 0 here — it is broken, not flaky — and is caught by
the consistently-failing rule instead (§5).

## 3. Failure recency (weight 15%)

Recent failures matter more than old ones. Executions are ordered oldest →
newest and weighted with exponential decay:

```text
w_i = 0.5 ** ((n - 1 - i) / half_life)     # half_life = 10 runs (default)
recency = Σ(w_i · bad_i) / Σ(w_i)          # bad = failed/error, range 0..1
```

Reasoning: a test failing *now* is actionable; a failure 50 runs ago that
never recurred is probably a fixed environment issue. The half-life of 10
runs means a failure 10 runs ago counts half as much as one today. The
parameter lives in `AnalysisConfig.recency_half_life_runs`.

Effect (verified): 8 passes + 2 failures scores **31.88** when the failures
are recent vs **30.23** when they are old (recency 0.259 vs 0.149).

## 4. Duration instability (weight 15%)

Coefficient of variation, bounded to 0..1:

```text
cv = pstdev(durations) / mean(durations)   # 0 if mean == 0 or n < 2
instability = cv / (1 + cv)
```

Deliberate guardrail: **a test with zero failed/error outcomes always scores
0**, no matter how variable its duration. A slow or variable-duration test
that always passes is flagged `is_slow` (mean > `SLOW_TEST_THRESHOLD`) but
never flaky. Verified: 10 passes at 8.0 s → score 0.00, `STABLE`, `is_slow`.

## 5. Flakiness score and classification

```text
score = 100 * (0.70 * inconsistency + 0.15 * recency + 0.15 * instability)
```

Weights were validated against the unit suite: inconsistency must dominate
(a 50/50 test reaches 77.76 = HIGHLY_FLAKY on inconsistency alone), while
recency/duration only nudge borderline cases. All thresholds configurable
via environment (`MIN_SAMPLE_SIZE`, `FLAKY_SCORE_THRESHOLD=40`,
`HIGHLY_FLAKY_SCORE_THRESHOLD=70`, `SLOW_TEST_THRESHOLD=5`,
`CONSISTENTLY_FAILING_THRESHOLD=0.95`).

Classification order:

| Condition | Classification |
|---|---|
| sample < `MIN_SAMPLE_SIZE` | INSUFFICIENT_DATA |
| failure_rate ≥ 0.95 | CONSISTENTLY_FAILING |
| score ≥ 70 | HIGHLY_FLAKY |
| score ≥ 40 | SUSPECTED_FLAKY |
| no failures/errors | STABLE |
| otherwise | MOSTLY_STABLE |

Verified examples (10 executions, defaults):

| History | Score | Classification |
|---|---|---|
| 10 × pass | 0.00 | STABLE |
| 5 pass / 5 fail | 77.76 | HIGHLY_FLAKY |
| 9 pass / 1 fail | 16.01 | MOSTLY_STABLE |
| 10 × fail | 15.00 | CONSISTENTLY_FAILING |
| 8 pass + 2 recent fail | 31.88 | MOSTLY_STABLE |

Note the all-fail row: its score (15.00, from recency alone) is *below* every
flaky threshold — the CONSISTENTLY_FAILING verdict comes from the failure-rate
rule, exactly as intended.

## 6. Newly-flaky and persistently-flaky

- **Newly flaky**: split history into older vs. last 10 runs (`recent_window_runs`).
  True when the older part classifies STABLE/MOSTLY_STABLE and the recent part
  classifies SUSPECTED/HIGHLY_FLAKY (each part needs `MIN_SAMPLE_SIZE` samples).
- **Persistently flaky**: split history into 3 consecutive windows
  (`persistent_windows`); true when ≥ 2 windows classify flaky
  (`persistent_flaky_min_windows`). All 3 windows need sufficient samples,
  otherwise false (not enough evidence).

## 7. Trends

Each history is split in half (older vs. recent) and compared:

- `pass_rate_delta` = recent pass rate − older pass rate
- `duration_delta` = recent median − older median
- `score_delta` = recent score − older score

Verified: all-fail → all-pass gives `pass_rate_delta = +1.0`, `score_delta < 0`.
