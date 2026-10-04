"""Phase 5 tests: demo generator, evaluation, flakyctl CLI."""

from __future__ import annotations

import json
from pathlib import Path

from app.analysis.service import AnalysisConfig, analyze_test_case
from app.cli import cmd_analyze, cmd_ingest, cmd_list_flaky, open_session
from app.demo.evaluation import evaluate
from app.demo.generator import (
    build_roster,
    outcome_for,
    seed_demo,
)
from app.models import TestCase

CONFIG = AnalysisConfig()


def test_roster_covers_all_archetypes():
    roster = build_roster()
    assert 20 <= len(roster) <= 50
    truths = [t.truth for t in roster]
    assert truths.count("stable") >= 10
    assert truths.count("flaky") == 9
    assert truths.count("consistently_failing") == 3
    names = [t.test_name for t in roster]
    assert len(set(names)) == len(names)


def test_outcome_patterns_are_deterministic():
    roster = {t.test_name: t for t in build_roster()}
    first = [outcome_for(t, i, 50) for i, t in enumerate(build_roster())]
    second = [outcome_for(t, i, 50) for i, t in enumerate(build_roster())]
    assert first == second

    assert outcome_for(roster["test_payment_3ds"], 0, 50).status == "failed"
    assert outcome_for(roster["test_login_valid"], 0, 50).status == "passed"
    assert outcome_for(roster["test_new_feature_flag"], 0, 50) is None
    assert outcome_for(roster["test_new_feature_flag"], 49, 50).status == "passed"
    assert outcome_for(roster["test_safari_only_ui"], 4, 50).status == "skipped"
    assert outcome_for(roster["test_safari_only_ui"], 0, 50).status == "passed"
    late = [outcome_for(roster["test_checkout_coupon"], i, 50).status for i in range(50)]
    assert set(late[:35]) == {"passed"}
    assert "failed" in late[35:]


def test_evaluation_metrics():
    truth = {"a": "flaky", "b": "flaky", "c": "stable", "d": "consistently_failing"}
    result = evaluate({"a": True, "b": False, "c": False, "d": False}, truth)
    assert (result.true_positives, result.false_negatives) == (1, 1)
    assert (result.true_negatives, result.false_positives) == (2, 0)
    assert result.precision == 1.0
    assert result.recall == 0.5

    empty = evaluate({}, {})
    assert empty.total == 0 and empty.precision == 0.0 and empty.recall == 0.0


def _seeded_session(tmp_path: Path, runs: int = 30):
    db_url = f"sqlite:///{tmp_path}/demo.db"
    from app.cli import ensure_schema

    ensure_schema(db_url)
    session = open_session(db_url)
    gt_path = tmp_path / "ground_truth.json"
    summary = seed_demo(session, project="test-demo", runs=runs, ground_truth_path=gt_path)
    return session, summary, gt_path


def test_seed_demo_end_to_end_with_perfect_detection(tmp_path: Path):
    session, summary, gt_path = _seeded_session(tmp_path)
    try:
        assert summary["runs"] == 30 and summary["tests"] == 30
        truth = json.loads(gt_path.read_text())
        assert len(truth) == 30

        result = cmd_analyze(session, "test-demo", gt_path, CONFIG)
        assert len(result["analyses"]) == 30
        by_key = {a.unique_key: a for a in result["analyses"]}
        assert by_key["test-demo::tests.test_payments::test_payment_timeout"].classification in (
            "SUSPECTED_FLAKY",
            "HIGHLY_FLAKY",
        )
        assert by_key["test-demo::tests.test_auth::test_login_valid"].classification == "STABLE"
        assert (
            by_key["test-demo::tests.test_payments::test_payment_3ds"].classification
            == "CONSISTENTLY_FAILING"
        )
        assert (
            by_key["test-demo::tests.test_feature::test_new_feature_flag"].classification
            == "INSUFFICIENT_DATA"
        )

        eval_result = result["eval"]
        assert eval_result is not None
        assert eval_result.false_positives == 0
        assert eval_result.false_negatives == 0
        assert eval_result.precision == 1.0
        assert eval_result.recall == 1.0

        flagged = cmd_list_flaky(session, "test-demo", None, 20, CONFIG)
        assert len(flagged) == 9
        scores = [a.flakiness_score for a in flagged]
        assert scores == sorted(scores, reverse=True)
    finally:
        session.close()


def test_seed_demo_refuses_second_run(tmp_path: Path):
    session, _, _ = _seeded_session(tmp_path)
    try:
        import pytest

        with pytest.raises(RuntimeError, match="already has runs"):
            seed_demo(session, project="test-demo", runs=30)
    finally:
        session.close()


def test_seed_demo_validates_run_count(tmp_path: Path):
    from app.cli import ensure_schema

    db_url = f"sqlite:///{tmp_path}/small.db"
    ensure_schema(db_url)
    session = open_session(db_url)
    try:
        import pytest

        with pytest.raises(ValueError, match="runs must be within"):
            seed_demo(session, runs=10)
    finally:
        session.close()


def test_cli_ingest_and_analyze_sample_xml(tmp_path: Path):
    from app.cli import ensure_schema

    db_url = f"sqlite:///{tmp_path}/ing.db"
    ensure_schema(db_url)
    session = open_session(db_url)
    try:
        result = cmd_ingest(
            session,
            Path(__file__).resolve().parent.parent.parent / "demo" / "sample-results.xml",
            project="sample",
            run_number=1,
        )
        assert result["summary"]["total"] == 5
        case = session.query(TestCase).filter_by(test_name="test_charge").one()
        analysis = analyze_test_case(session, case.id, CONFIG)
        assert analysis.classification == "INSUFFICIENT_DATA"
    finally:
        session.close()
