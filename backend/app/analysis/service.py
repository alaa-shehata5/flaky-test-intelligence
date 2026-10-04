"""Analysis service: executions -> per-test QA intelligence."""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.analysis import classification, scoring, statistics
from app.analysis.classification import Classification, TrendResult
from app.analysis.statistics import ExecutionInput
from app.core.config import Settings, get_settings
from app.models import TestCase, TestExecution


@dataclass(frozen=True)
class AnalysisConfig:
    min_sample_size: int = 5
    flaky_threshold: float = 40.0
    highly_flaky_threshold: float = 70.0
    slow_threshold: float = 5.0
    consistently_failing_threshold: float = 0.95
    recency_half_life_runs: float = 10.0
    recent_window_runs: int = 10
    persistent_windows: int = 3
    persistent_flaky_min_windows: int = 2

    @classmethod
    def from_settings(cls, settings: Settings) -> AnalysisConfig:
        return cls(
            min_sample_size=settings.min_sample_size,
            flaky_threshold=settings.flaky_score_threshold,
            highly_flaky_threshold=settings.highly_flaky_score_threshold,
            slow_threshold=settings.slow_test_threshold,
            consistently_failing_threshold=settings.consistently_failing_threshold,
        )


class TestAnalysis(BaseModel):
    test_case_id: int
    unique_key: str
    sample_size: int
    passed: int
    failed: int
    error: int
    skipped: int
    pass_rate: float
    failure_rate: float
    duration_min: float
    duration_max: float
    duration_mean: float
    duration_median: float
    duration_p95: float
    duration_stddev: float
    inconsistency: float
    recency: float
    duration_instability: float
    flakiness_score: float
    classification: Classification
    newly_flaky: bool
    persistently_flaky: bool
    is_slow: bool
    pass_rate_delta: float
    duration_delta: float
    score_delta: float


def _inputs(executions: list[TestExecution]) -> list[ExecutionInput]:
    ordered = sorted(executions, key=lambda e: (e.executed_at, e.id or 0))
    return [
        ExecutionInput(
            status=e.status,
            duration=e.duration,
            executed_at=e.executed_at,
            id=e.id or 0,
        )
        for e in ordered
    ]


def _classify_inputs(
    inputs: list[ExecutionInput], config: AnalysisConfig
) -> tuple[statistics.BasicStats, float, Classification]:
    basic = statistics.compute_basic(inputs)
    durations = [e.duration for e in inputs if e.status != "skipped"]
    score = scoring.flakiness_score(
        basic.pass_rate, inputs, durations, config.recency_half_life_runs
    )
    cls = classification.classify(
        basic,
        score,
        config.min_sample_size,
        config.flaky_threshold,
        config.highly_flaky_threshold,
        config.consistently_failing_threshold,
    )
    return basic, score, cls


def analyze_inputs(inputs: list[ExecutionInput], config: AnalysisConfig | None = None) -> dict:
    """Pure analysis over ordered execution inputs (no DB access)."""
    config = config or AnalysisConfig.from_settings(get_settings())
    basic, score, cls = _classify_inputs(inputs, config)
    durations = statistics.compute_durations(inputs)
    signalled_durations = [e.duration for e in inputs if e.status != "skipped"]

    half = len(inputs) // 2
    older, recent_window = inputs[:half], inputs[half:]
    recent = inputs[-config.recent_window_runs :] if inputs else []
    older_for_newly = inputs[: len(inputs) - len(recent)] if recent else []
    trends: TrendResult = classification.compute_trends(older, recent_window)

    newly = (
        classification.is_newly_flaky(
            older_for_newly,
            recent,
            config.min_sample_size,
            config.flaky_threshold,
            config.highly_flaky_threshold,
            config.consistently_failing_threshold,
        )
        if older_for_newly and recent
        else False
    )

    windows: list[Classification] = []
    if inputs:
        chunk = max(1, len(inputs) // config.persistent_windows)
        for i in range(config.persistent_windows):
            part = (
                inputs[i * chunk :]
                if i == config.persistent_windows - 1
                else inputs[i * chunk : (i + 1) * chunk]
            )
            if statistics.compute_basic(part).sample_size >= config.min_sample_size:
                windows.append(_classify_inputs(part, config)[2])
    persistent = (
        classification.is_persistently_flaky(windows, config.persistent_flaky_min_windows)
        if len(windows) == config.persistent_windows
        else False
    )

    return {
        "sample_size": basic.sample_size,
        "passed": basic.passed,
        "failed": basic.failed,
        "error": basic.error,
        "skipped": basic.skipped,
        "pass_rate": basic.pass_rate,
        "failure_rate": basic.failure_rate,
        "durations": durations,
        "inconsistency": scoring.outcome_inconsistency(basic.pass_rate),
        "recency": scoring.recency_score(inputs, config.recency_half_life_runs),
        "duration_instability": scoring.duration_instability(signalled_durations),
        "flakiness_score": score,
        "classification": cls,
        "newly_flaky": newly,
        "persistently_flaky": persistent,
        "is_slow": durations.mean > config.slow_threshold if durations.count else False,
        "trends": trends,
    }


def analyze_test_case(
    session: Session,
    test_case_id: int,
    config: AnalysisConfig | None = None,
) -> TestAnalysis:
    test_case = session.get(TestCase, test_case_id)
    if test_case is None:
        raise ValueError(f"test case {test_case_id} not found")
    executions = list(
        session.scalars(
            select(TestExecution)
            .where(TestExecution.test_case_id == test_case_id)
            .order_by(TestExecution.executed_at, TestExecution.id)
        )
    )
    result = analyze_inputs(_inputs(executions), config)
    durations = result["durations"]
    trends = result["trends"]
    return TestAnalysis(
        test_case_id=test_case.id,
        unique_key=test_case.unique_key,
        sample_size=result["sample_size"],
        passed=result["passed"],
        failed=result["failed"],
        error=result["error"],
        skipped=result["skipped"],
        pass_rate=result["pass_rate"],
        failure_rate=result["failure_rate"],
        duration_min=durations.min,
        duration_max=durations.max,
        duration_mean=durations.mean,
        duration_median=durations.median,
        duration_p95=durations.p95,
        duration_stddev=durations.stddev,
        inconsistency=result["inconsistency"],
        recency=result["recency"],
        duration_instability=result["duration_instability"],
        flakiness_score=result["flakiness_score"],
        classification=result["classification"],
        newly_flaky=result["newly_flaky"],
        persistently_flaky=result["persistently_flaky"],
        is_slow=result["is_slow"],
        pass_rate_delta=trends.pass_rate_delta,
        duration_delta=trends.duration_median_delta,
        score_delta=trends.score_delta,
    )


def analyze_project(
    session: Session,
    project_id: int,
    config: AnalysisConfig | None = None,
) -> list[TestAnalysis]:
    case_ids = session.scalars(
        select(TestCase.id).where(TestCase.project_id == project_id).order_by(TestCase.id)
    ).all()
    return [analyze_test_case(session, case_id, config) for case_id in case_ids]
