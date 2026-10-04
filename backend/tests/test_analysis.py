"""Phase 4 tests: statistics, scoring, classification, trends, service."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.analysis import classification, scoring
from app.analysis.classification import (
    is_newly_flaky,
    is_persistently_flaky,
)
from app.analysis.service import AnalysisConfig, analyze_inputs, analyze_test_case
from app.analysis.statistics import ExecutionInput, compute_basic, compute_durations
from app.ingestion.schemas import TestCaseResult, TestRunResult
from app.ingestion.service import persist_run
from app.models import TestCase

TestCaseResult.__test__ = False  # pydantic schema, not a test class
TestRunResult.__test__ = False  # pydantic schema, not a test class

BASE = datetime(2026, 1, 1, tzinfo=UTC)
CONFIG = AnalysisConfig()


def _inputs(statuses: list[str], durations: list[float] | None = None) -> list[ExecutionInput]:
    return [
        ExecutionInput(
            status=status,
            duration=(durations[i] if durations else 0.5),
            executed_at=BASE + timedelta(hours=i),
            id=i,
        )
        for i, status in enumerate(statuses)
    ]


def _analyzed(statuses: list[str], durations: list[float] | None = None) -> dict:
    return analyze_inputs(_inputs(statuses, durations), CONFIG)


def test_all_pass_is_stable_with_zero_score():
    result = _analyzed(["passed"] * 10)
    assert result["classification"] == "STABLE"
    assert result["flakiness_score"] == 0.0
    assert result["pass_rate"] == 1.0
    assert result["newly_flaky"] is False


def test_all_fail_is_consistently_failing():
    result = _analyzed(["failed"] * 10)
    assert result["classification"] == "CONSISTENTLY_FAILING"
    assert result["failure_rate"] == 1.0


def test_all_error_is_consistently_failing():
    result = _analyzed(["error"] * 10)
    assert result["classification"] == "CONSISTENTLY_FAILING"


def test_fifty_fifty_is_highly_flaky():
    result = _analyzed(["passed", "failed"] * 5)
    assert result["classification"] == "HIGHLY_FLAKY"
    assert result["inconsistency"] == 1.0
    assert result["flakiness_score"] >= 70.0


def test_low_sample_size_is_insufficient_data():
    result = _analyzed(["passed", "failed", "passed"])
    assert result["classification"] == "INSUFFICIENT_DATA"
    assert result["sample_size"] == 3


def test_mostly_passing_is_mostly_stable():
    result = _analyzed(["passed"] * 9 + ["failed"])
    assert result["classification"] == "MOSTLY_STABLE"
    assert result["flakiness_score"] < 40.0


def test_mostly_failing_below_threshold_is_not_consistently_failing():
    result = _analyzed(["passed"] + ["failed"] * 9)
    assert result["failure_rate"] == 0.9
    assert result["classification"] == "MOSTLY_STABLE"


def test_failure_rate_at_threshold_is_consistently_failing():
    result = _analyzed(["passed"] + ["failed"] * 19)
    assert result["failure_rate"] == 0.95
    assert result["classification"] == "CONSISTENTLY_FAILING"


def test_recent_failures_score_higher_than_old_failures():
    old_failures = _analyzed(["failed", "failed"] + ["passed"] * 8)
    recent_failures = _analyzed(["passed"] * 8 + ["failed", "failed"])
    assert recent_failures["recency"] > old_failures["recency"]
    assert recent_failures["flakiness_score"] > old_failures["flakiness_score"]


def test_slow_stable_test_is_not_flaky_but_slow():
    result = _analyzed(["passed"] * 10, durations=[8.0] * 10)
    assert result["classification"] == "STABLE"
    assert result["flakiness_score"] == 0.0
    assert result["is_slow"] is True


def test_variable_duration_without_failures_is_not_flaky():
    durations = [0.2, 0.5, 1.0, 2.0, 4.0, 0.3, 9.0, 1.5, 0.8, 3.0]
    result = _analyzed(["passed"] * 10, durations=durations)
    assert result["duration_instability"] > 0.3
    assert result["flakiness_score"] == 0.0
    assert result["classification"] == "STABLE"


def test_duration_statistics_known_values():
    stats = compute_durations(_inputs(["passed"] * 4, durations=[1.0, 2.0, 3.0, 4.0]))
    assert (stats.min, stats.max) == (1.0, 4.0)
    assert stats.mean == 2.5
    assert stats.median == 2.5
    assert stats.p95 == 4.0
    assert stats.stddev == 1.118033988749895


def test_duration_statistics_empty():
    stats = compute_durations([])
    assert stats.count == 0 and stats.mean == 0.0


def test_inconsistency_formula():
    assert scoring.outcome_inconsistency(1.0) == 0.0
    assert scoring.outcome_inconsistency(0.0) == 0.0
    assert scoring.outcome_inconsistency(0.5) == 1.0
    assert scoring.outcome_inconsistency(0.9) == pytest.approx(0.2)


def test_basic_stats_exclude_skipped_from_sample():
    basic = compute_basic(_inputs(["passed"] * 5 + ["skipped"] * 5))
    assert basic.sample_size == 5
    assert basic.skipped == 5
    assert basic.pass_rate == 1.0


def test_newly_flaky_detection():
    stable_then_flaky = _inputs(["passed"] * 10 + ["passed", "failed"] * 5)
    result = analyze_inputs(stable_then_flaky, CONFIG)
    assert result["newly_flaky"] is True

    always_stable = analyze_inputs(_inputs(["passed"] * 20), CONFIG)
    assert always_stable["newly_flaky"] is False

    always_flaky = analyze_inputs(_inputs(["passed", "failed"] * 10), CONFIG)
    assert always_flaky["newly_flaky"] is False


def test_is_newly_flaky_helper():
    old = _inputs(["passed"] * 10)
    new = _inputs(["passed", "failed"] * 5)
    assert (
        is_newly_flaky(
            old,
            new,
            CONFIG.min_sample_size,
            CONFIG.flaky_threshold,
            CONFIG.highly_flaky_threshold,
            CONFIG.consistently_failing_threshold,
        )
        is True
    )
    assert (
        is_newly_flaky(
            new,
            new,
            CONFIG.min_sample_size,
            CONFIG.flaky_threshold,
            CONFIG.highly_flaky_threshold,
            CONFIG.consistently_failing_threshold,
        )
        is False
    )


def test_persistently_flaky_detection():
    assert is_persistently_flaky(["SUSPECTED_FLAKY", "HIGHLY_FLAKY", "SUSPECTED_FLAKY"]) is True
    assert is_persistently_flaky(["STABLE", "STABLE", "SUSPECTED_FLAKY"]) is False
    assert is_persistently_flaky(["STABLE", "STABLE", "STABLE"]) is False

    chronic = analyze_inputs(_inputs(["passed", "failed"] * 15), CONFIG)
    assert chronic["persistently_flaky"] is True
    assert chronic["newly_flaky"] is False

    recent_only = analyze_inputs(_inputs(["passed"] * 20 + ["passed", "failed"] * 5), CONFIG)
    assert recent_only["persistently_flaky"] is False
    assert recent_only["newly_flaky"] is True


def test_trends_improving_and_regressing():
    improving = classification.compute_trends(_inputs(["failed"] * 10), _inputs(["passed"] * 10))
    assert improving.pass_rate_delta == 1.0
    assert improving.failure_rate_delta == -1.0
    assert improving.score_delta < 0

    regressing = classification.compute_trends(_inputs(["passed"] * 10), _inputs(["failed"] * 10))
    assert regressing.pass_rate_delta == -1.0
    assert regressing.score_delta > 0


def test_service_end_to_end_from_ingested_runs(db_session):
    for run_number in (1, 2, 3):
        cases = [
            TestCaseResult(
                classname="s.T",
                test_name="t_flaky",
                status="failed" if run_number % 2 == 0 else "passed",
                duration=0.5,
            ),
            TestCaseResult(classname="s.T", test_name="t_stable", status="passed", duration=0.5),
        ]
        persist_run(
            db_session,
            TestRunResult(project="svc", run_number=run_number, cases=cases),
        )
    # 3 samples < min_sample_size 5 -> INSUFFICIENT_DATA for both.
    flaky_id = db_session.query(TestCase).filter_by(test_name="t_flaky").one().id
    analysis = analyze_test_case(db_session, flaky_id, CONFIG)
    assert analysis.classification == "INSUFFICIENT_DATA"
    assert analysis.sample_size == 3
    assert analysis.unique_key == "svc::s.T::t_flaky"


def test_service_classifies_with_enough_history(db_session):
    for run_number in range(1, 11):
        persist_run(
            db_session,
            TestRunResult(
                project="svc2",
                run_number=run_number,
                cases=[
                    TestCaseResult(
                        classname="s.T",
                        test_name="t_coin",
                        status="passed" if run_number % 2 else "failed",
                        duration=0.5,
                    )
                ],
            ),
        )
    case_id = db_session.query(TestCase).filter_by(test_name="t_coin").one().id
    analysis = analyze_test_case(db_session, case_id, CONFIG)
    assert analysis.classification == "HIGHLY_FLAKY"
    assert analysis.sample_size == 10
    assert analysis.pass_rate == 0.5
