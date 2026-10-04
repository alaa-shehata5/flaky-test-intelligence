# Detection Algorithm (planned — Phase 0)

> Status: initial skeleton. Full formula, parameters, and reasoning will be
> documented here in Phase 4 after the analysis engine is built and tested.

## Planned sections

- [ ] Pipeline: raw executions → statistics → inconsistency → recency → duration instability → score → classification
- [ ] Basic + duration statistics definitions
- [ ] Outcome inconsistency formula (starting point: `1 - abs(pass_rate - 0.5) * 2`, to be validated)
- [ ] Recency weighting (e.g. exponential decay): formula, parameters, reasoning
- [ ] Duration instability metric (stddev / CV / percentile spread); slow ≠ flaky
- [ ] Composite 0–100 score + weights (conceptual: inconsistency 70%, recency 15%, duration 15%)
- [ ] Classification thresholds: INSUFFICIENT_DATA, STABLE, MOSTLY_STABLE, SUSPECTED_FLAKY, HIGHLY_FLAKY, CONSISTENTLY_FAILING
- [ ] Newly-flaky + persistently-flaky rules
- [ ] Worked examples (real outputs only)
