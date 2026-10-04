"""Deterministic synthetic demo data generator.

Produces a fixed roster of tests with scripted behaviors (no uncontrolled
randomness: outcomes are pure functions of the run index), persists them as
CI runs via the ingestion service, and writes ground-truth labels used only
for detector evaluation — never for scoring.

All generated failure messages are marked as synthetic demo data.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Literal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ingestion.schemas import TestCaseResult, TestRunResult
from app.ingestion.service import persist_run
from app.models import Project, TestRun

GroundTruthLabel = Literal["stable", "flaky", "consistently_failing"]

SYNTHETIC_TAG = "(synthetic demo data)"
BASE_TIME = datetime(2026, 1, 1, tzinfo=UTC)
DEFAULT_PROJECT = "demo-project"
DEFAULT_RUNS = 50
MIN_RUNS, MAX_RUNS = 30, 100


@dataclass(frozen=True)
class DemoTest:
    test_name: str
    classname: str
    suite_name: str
    truth: GroundTruthLabel


def build_roster() -> list[DemoTest]:
    """Fixed 30-test roster covering every behavior archetype."""
    roster = [
        DemoTest("test_login_valid", "tests.test_auth", "auth", "stable"),
        DemoTest("test_logout", "tests.test_auth", "auth", "stable"),
        DemoTest("test_cart_add_item", "tests.test_cart", "cart", "stable"),
        DemoTest("test_cart_remove_item", "tests.test_cart", "cart", "stable"),
        DemoTest("test_search_basic", "tests.test_search", "search", "stable"),
        DemoTest("test_profile_update", "tests.test_profile", "profile", "stable"),
        DemoTest("test_orders_list", "tests.test_orders", "orders", "stable"),
        DemoTest("test_health_ping", "tests.test_health", "health", "stable"),
        DemoTest("test_pagination", "tests.test_search", "search", "stable"),
        DemoTest("test_sorting", "tests.test_search", "search", "stable"),
        DemoTest("test_filters", "tests.test_search", "search", "stable"),
        DemoTest("test_csv_download", "tests.test_reports", "reports", "stable"),
        DemoTest("test_report_export_csv", "tests.test_reports", "reports", "stable"),
        DemoTest("test_bulk_import", "tests.test_reports", "reports", "stable"),
        DemoTest("test_search_fuzzy", "tests.test_search", "search", "stable"),
        DemoTest("test_payment_3ds", "tests.test_payments", "payments", "consistently_failing"),
        DemoTest("test_legacy_sso", "tests.test_auth", "auth", "consistently_failing"),
        DemoTest("test_pdf_render_arabic", "tests.test_reports", "reports", "consistently_failing"),
        DemoTest("test_payment_timeout", "tests.test_payments", "payments", "flaky"),
        DemoTest("test_search_ranking", "tests.test_search", "search", "flaky"),
        DemoTest("test_notifications_push", "tests.test_notifications", "notifications", "flaky"),
        DemoTest("test_inventory_sync", "tests.test_inventory", "inventory", "flaky"),
        DemoTest("test_session_refresh", "tests.test_auth", "auth", "flaky"),
        DemoTest("test_rate_limit_retry", "tests.test_api", "api", "flaky"),
        DemoTest("test_checkout_coupon", "tests.test_cart", "cart", "flaky"),
        DemoTest("test_webhook_delivery", "tests.test_api", "api", "flaky"),
        DemoTest("test_db_pool_exhaustion", "tests.test_db", "db", "flaky"),
        DemoTest("test_safari_only_ui", "tests.test_ui", "ui", "stable"),
        DemoTest("test_gpu_render", "tests.test_ui", "ui", "stable"),
        DemoTest("test_new_feature_flag", "tests.test_feature", "feature", "stable"),
    ]
    assert len(roster) == 30
    return roster


def outcome_for(test: DemoTest, run_index: int, total_runs: int) -> TestCaseResult | None:
    """Deterministic outcome of one demo test in one run (None = absent)."""
    name = test.test_name

    if name == "test_new_feature_flag":
        if run_index < total_runs - 2:
            return None
        return TestCaseResult(
            suite_name=test.suite_name,
            classname=test.classname,
            test_name=name,
            status="passed",
            duration=0.3,
        )
    if name in ("test_report_export_csv", "test_bulk_import"):
        duration = 8.2 if name == "test_report_export_csv" else 11.5
        return TestCaseResult(
            suite_name=test.suite_name,
            classname=test.classname,
            test_name=name,
            status="passed",
            duration=duration,
        )
    if name == "test_search_fuzzy":
        duration = [0.2, 1.5, 4.0, 9.0][run_index % 4]
        return TestCaseResult(
            suite_name=test.suite_name,
            classname=test.classname,
            test_name=name,
            status="passed",
            duration=duration,
        )
    if name in ("test_payment_3ds", "test_legacy_sso", "test_pdf_render_arabic"):
        return TestCaseResult(
            suite_name=test.suite_name,
            classname=test.classname,
            test_name=name,
            status="failed",
            duration=0.6,
            failure_message=f"AssertionError: known broken behavior {SYNTHETIC_TAG}",
            failure_type="AssertionError",
        )
    if name in (
        "test_payment_timeout",
        "test_search_ranking",
        "test_notifications_push",
        "test_inventory_sync",
    ):
        offset = {
            "test_payment_timeout": 0,
            "test_search_ranking": 1,
            "test_notifications_push": 2,
            "test_inventory_sync": 0,
        }[name]
        if (run_index + offset) % 3 == 0:
            return TestCaseResult(
                suite_name=test.suite_name,
                classname=test.classname,
                test_name=name,
                status="failed",
                duration=2.5,
                failure_message=f"TimeoutError: downstream timeout after 2000ms {SYNTHETIC_TAG}",
                failure_type="TimeoutError",
            )
    if name in ("test_session_refresh", "test_rate_limit_retry"):
        if run_index % 2 == 1:
            return TestCaseResult(
                suite_name=test.suite_name,
                classname=test.classname,
                test_name=name,
                status="failed",
                duration=0.9,
                failure_message=f"AssertionError: race on refresh {SYNTHETIC_TAG}",
                failure_type="AssertionError",
            )
    if name == "test_checkout_coupon":
        if run_index >= int(total_runs * 0.7) and run_index % 2 == 0:
            return TestCaseResult(
                suite_name=test.suite_name,
                classname=test.classname,
                test_name=name,
                status="failed",
                duration=1.1,
                failure_message=f"AssertionError: coupon rejected intermittently {SYNTHETIC_TAG}",
                failure_type="AssertionError",
            )
    if name == "test_webhook_delivery":
        if run_index >= int(total_runs * 0.7) and run_index % 3 == 0:
            return TestCaseResult(
                suite_name=test.suite_name,
                classname=test.classname,
                test_name=name,
                status="failed",
                duration=3.0,
                failure_message=f"TimeoutError: webhook not delivered {SYNTHETIC_TAG}",
                failure_type="TimeoutError",
            )
    if name == "test_db_pool_exhaustion":
        if run_index % 3 == 2:
            return TestCaseResult(
                suite_name=test.suite_name,
                classname=test.classname,
                test_name=name,
                status="error",
                duration=5.0,
                failure_message=f"PoolExhausted: no connection available {SYNTHETIC_TAG}",
                failure_type="PoolExhausted",
            )
    if name == "test_safari_only_ui":
        if run_index % 5 == 4:
            return TestCaseResult(
                suite_name=test.suite_name,
                classname=test.classname,
                test_name=name,
                status="skipped",
                duration=0.0,
            )
    if name == "test_gpu_render":
        if run_index % 7 == 6:
            return TestCaseResult(
                suite_name=test.suite_name,
                classname=test.classname,
                test_name=name,
                status="skipped",
                duration=0.0,
            )
    # Default: stable pass with deterministic fast duration.
    duration = round(0.1 + ((run_index * 37 + len(name) * 13) % 9) / 10, 2)
    return TestCaseResult(
        suite_name=test.suite_name,
        classname=test.classname,
        test_name=name,
        status="passed",
        duration=duration,
    )


def build_ground_truth(project: str, roster: list[DemoTest]) -> dict[str, GroundTruthLabel]:
    return {f"{project}::{t.classname}::{t.test_name}": t.truth for t in roster}


def seed_demo(
    session: Session,
    project: str = DEFAULT_PROJECT,
    runs: int = DEFAULT_RUNS,
    ground_truth_path: Path | None = None,
) -> dict:
    """Persist deterministic demo history. Raises RuntimeError if present."""
    if not MIN_RUNS <= runs <= MAX_RUNS:
        raise ValueError(f"runs must be within {MIN_RUNS}..{MAX_RUNS}")
    project_row = session.scalar(select(Project).where(Project.name == project))
    if project_row is not None and (
        session.scalar(select(TestRun.id).where(TestRun.project_id == project_row.id)) is not None
    ):
        raise RuntimeError(
            f"project '{project}' already has runs; refusing to seed twice "
            "(reset the database to re-seed)"
        )
    roster = build_roster()
    for run_index in range(runs):
        cases = [case for t in roster if (case := outcome_for(t, run_index, runs)) is not None]
        executed_at = BASE_TIME + timedelta(hours=run_index)
        persist_run(
            session,
            TestRunResult(
                project=project,
                run_number=run_index + 1,
                branch="main",
                commit_sha=f"abc123{run_index + 1:06d}",
                workflow_name="ci",
                environment="ci",
                cases=cases,
            ),
            executed_at=executed_at,
        )
    ground_truth = build_ground_truth(project, roster)
    if ground_truth_path is not None:
        ground_truth_path.parent.mkdir(parents=True, exist_ok=True)
        ground_truth_path.write_text(json.dumps(ground_truth, indent=2) + "\n")
    return {
        "project": project,
        "runs": runs,
        "tests": len(roster),
        "ground_truth_path": str(ground_truth_path) if ground_truth_path else None,
    }
