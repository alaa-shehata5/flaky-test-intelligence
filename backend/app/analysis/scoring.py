"""Flakiness scoring.

Composite 0-100 score (see docs/detection-algorithm.md)::

    score = 100 * (0.70 * inconsistency
                 + 0.15 * recency
                 + 0.15 * duration_instability)

- ``inconsistency = 1 - abs(pass_rate - 0.5) * 2`` (0 = unanimous, 1 = 50/50).
- ``recency``: failure fraction with exponential-decay weights so recent
  failures matter more. Weight of the i-th oldest of n executions is
  ``0.5 ** ((n - 1 - i) / half_life)``.
- ``duration_instability = cv / (1 + cv)`` with ``cv = pstdev / mean``
  (0 when the mean is 0 or fewer than 2 samples).
- A test with zero failed/error outcomes always scores 0: variable or slow
  duration alone must never flag a test as flaky.
"""

from __future__ import annotations

import statistics

from app.analysis.statistics import BAD_STATUSES, ExecutionInput, _ordered

INCONSISTENCY_WEIGHT = 0.70
RECENCY_WEIGHT = 0.15
DURATION_WEIGHT = 0.15
DEFAULT_RECENCY_HALF_LIFE_RUNS = 10.0


def outcome_inconsistency(pass_rate: float) -> float:
    return max(0.0, min(1.0, 1.0 - abs(pass_rate - 0.5) * 2.0))


def recency_score(
    executions: list[ExecutionInput],
    half_life_runs: float = DEFAULT_RECENCY_HALF_LIFE_RUNS,
) -> float:
    signalled = [e for e in _ordered(executions) if e.status != "skipped"]
    n = len(signalled)
    if n == 0:
        return 0.0
    weights = [0.5 ** ((n - 1 - i) / half_life_runs) for i in range(n)]
    bad = [1.0 if e.status in BAD_STATUSES else 0.0 for e in signalled]
    return sum(w * b for w, b in zip(weights, bad, strict=True)) / sum(weights)


def duration_instability(durations: list[float]) -> float:
    n = len(durations)
    if n < 2:
        return 0.0
    mean = statistics.fmean(durations)
    if mean <= 0:
        return 0.0
    cv = statistics.pstdev(durations) / mean
    return cv / (1.0 + cv)


def flakiness_score(
    pass_rate: float,
    executions: list[ExecutionInput],
    durations: list[float] | None = None,
    half_life_runs: float = DEFAULT_RECENCY_HALF_LIFE_RUNS,
) -> float:
    signalled = [e for e in executions if e.status != "skipped"]
    if not any(e.status in BAD_STATUSES for e in signalled):
        return 0.0
    if durations is None:
        durations = [e.duration for e in signalled]
    score = 100.0 * (
        INCONSISTENCY_WEIGHT * outcome_inconsistency(pass_rate)
        + RECENCY_WEIGHT * recency_score(executions, half_life_runs)
        + DURATION_WEIGHT * duration_instability(durations)
    )
    return round(max(0.0, min(100.0, score)), 2)
