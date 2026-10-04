"""Classification and trend analysis.

Classifications (see docs/detection-algorithm.md):
- INSUFFICIENT_DATA: sample below the minimum.
- CONSISTENTLY_FAILING: failure rate at/above the threshold.
- HIGHLY_FLAKY / SUSPECTED_FLAKY: score at/above the respective thresholds.
- STABLE: no failed/error outcomes.
- MOSTLY_STABLE: everything else (low-score, non-unanimous history).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.analysis import scoring, statistics
from app.analysis.statistics import ExecutionInput

Classification = Literal[
    "INSUFFICIENT_DATA",
    "STABLE",
    "MOSTLY_STABLE",
    "SUSPECTED_FLAKY",
    "HIGHLY_FLAKY",
    "CONSISTENTLY_FAILING",
]

FLAKY_CLASSIFICATIONS: tuple[str, ...] = ("SUSPECTED_FLAKY", "HIGHLY_FLAKY")
STABLE_CLASSIFICATIONS: tuple[str, ...] = ("STABLE", "MOSTLY_STABLE")


def classify(
    basic: statistics.BasicStats,
    score: float,
    min_sample_size: int,
    flaky_threshold: float,
    highly_flaky_threshold: float,
    consistently_failing_threshold: float,
) -> Classification:
    if basic.sample_size < min_sample_size:
        return "INSUFFICIENT_DATA"
    if basic.failure_rate >= consistently_failing_threshold:
        return "CONSISTENTLY_FAILING"
    if score >= highly_flaky_threshold:
        return "HIGHLY_FLAKY"
    if score >= flaky_threshold:
        return "SUSPECTED_FLAKY"
    if basic.failed == 0 and basic.error == 0:
        return "STABLE"
    return "MOSTLY_STABLE"


def _classify_window(
    executions: list[ExecutionInput],
    min_sample_size: int,
    flaky_threshold: float,
    highly_flaky_threshold: float,
    consistently_failing_threshold: float,
) -> Classification:
    basic = statistics.compute_basic(executions)
    durations = [e.duration for e in executions if e.status != "skipped"]
    score = scoring.flakiness_score(basic.pass_rate, executions, durations)
    return classify(
        basic,
        score,
        min_sample_size,
        flaky_threshold,
        highly_flaky_threshold,
        consistently_failing_threshold,
    )


def is_newly_flaky(
    older: list[ExecutionInput],
    recent: list[ExecutionInput],
    min_sample_size: int,
    flaky_threshold: float,
    highly_flaky_threshold: float,
    consistently_failing_threshold: float,
) -> bool:
    """True when a previously stable test is flaky in the recent window."""
    older_class = _classify_window(
        older,
        min_sample_size,
        flaky_threshold,
        highly_flaky_threshold,
        consistently_failing_threshold,
    )
    recent_class = _classify_window(
        recent,
        min_sample_size,
        flaky_threshold,
        highly_flaky_threshold,
        consistently_failing_threshold,
    )
    return older_class in STABLE_CLASSIFICATIONS and recent_class in FLAKY_CLASSIFICATIONS


def is_persistently_flaky(windows: list[Classification], min_flaky_windows: int = 2) -> bool:
    """True when flakiness repeats across multiple analysis windows."""
    return sum(1 for w in windows if w in FLAKY_CLASSIFICATIONS) >= min_flaky_windows


@dataclass(frozen=True)
class TrendResult:
    pass_rate_delta: float
    duration_median_delta: float
    score_delta: float


def compute_trends(
    older: list[ExecutionInput],
    recent: list[ExecutionInput],
) -> TrendResult:
    """Compare the recent window against the older window (recent minus older)."""
    old_basic = statistics.compute_basic(older)
    new_basic = statistics.compute_basic(recent)
    old_durations = statistics.compute_durations(older)
    new_durations = statistics.compute_durations(recent)
    old_score = scoring.flakiness_score(
        old_basic.pass_rate, older, [e.duration for e in older if e.status != "skipped"]
    )
    new_score = scoring.flakiness_score(
        new_basic.pass_rate,
        recent,
        [e.duration for e in recent if e.status != "skipped"],
    )
    return TrendResult(
        pass_rate_delta=new_basic.pass_rate - old_basic.pass_rate,
        duration_median_delta=new_durations.median - old_durations.median,
        score_delta=new_score - old_score,
    )
