"""Basic and duration statistics over test execution history.

Conventions (see docs/detection-algorithm.md):
- ``sample_size`` counts non-skipped executions. Skipped results carry no
  pass/fail signal and are reported separately.
- ``pass_rate = passed / sample_size``,
  ``failure_rate = (failed + error) / sample_size``.
- Duration statistics cover non-skipped executions.
- p95 uses the nearest-rank method.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass
from datetime import datetime

BAD_STATUSES = ("failed", "error")


@dataclass(frozen=True)
class ExecutionInput:
    status: str
    duration: float
    executed_at: datetime
    id: int = 0


@dataclass(frozen=True)
class BasicStats:
    sample_size: int
    passed: int
    failed: int
    error: int
    skipped: int
    pass_rate: float
    failure_rate: float


@dataclass(frozen=True)
class DurationStats:
    count: int
    min: float
    max: float
    mean: float
    median: float
    p95: float
    stddev: float


def _ordered(executions: list[ExecutionInput]) -> list[ExecutionInput]:
    return sorted(executions, key=lambda e: (e.executed_at, e.id))


def _signalled(executions: list[ExecutionInput]) -> list[ExecutionInput]:
    return [e for e in executions if e.status != "skipped"]


def compute_basic(executions: list[ExecutionInput]) -> BasicStats:
    signalled = _signalled(executions)
    passed = sum(1 for e in signalled if e.status == "passed")
    failed = sum(1 for e in signalled if e.status == "failed")
    error = sum(1 for e in signalled if e.status == "error")
    skipped = sum(1 for e in executions if e.status == "skipped")
    sample = len(signalled)
    return BasicStats(
        sample_size=sample,
        passed=passed,
        failed=failed,
        error=error,
        skipped=skipped,
        pass_rate=(passed / sample) if sample else 0.0,
        failure_rate=((failed + error) / sample) if sample else 0.0,
    )


def compute_durations(executions: list[ExecutionInput]) -> DurationStats:
    values = sorted(e.duration for e in _signalled(executions))
    n = len(values)
    if n == 0:
        return DurationStats(0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    return DurationStats(
        count=n,
        min=values[0],
        max=values[-1],
        mean=statistics.fmean(values),
        median=statistics.median(values),
        p95=values[math.ceil(0.95 * n) - 1],
        stddev=statistics.pstdev(values) if n > 1 else 0.0,
    )
