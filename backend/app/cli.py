"""flakyctl: seed demo data, ingest JUnit XML, analyze, list flaky tests."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from alembic.config import Config
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from alembic import command as alembic_command
from app.analysis.classification import FLAKY_CLASSIFICATIONS
from app.analysis.service import AnalysisConfig, analyze_test_case
from app.core.config import get_settings
from app.demo.evaluation import evaluate
from app.demo.generator import DEFAULT_PROJECT, DEFAULT_RUNS, MAX_RUNS, MIN_RUNS, seed_demo
from app.ingestion.parser import MAX_JUNIT_BYTES, JUnitParseError, parse_junit
from app.ingestion.schemas import TestRunResult
from app.ingestion.service import DuplicateRunError, persist_run
from app.models import Project, TestCase

BACKEND_DIR = Path(__file__).resolve().parent.parent


def resolve_db_url(explicit: str | None = None) -> str:
    return explicit or os.environ.get("DATABASE_URL") or get_settings().database_url


def _alembic_ini() -> Path:
    """Locate alembic.ini in a dev checkout (backend/) or container (/app)."""
    for ini in (BACKEND_DIR / "alembic.ini", Path("/app/alembic.ini")):
        if ini.is_file():
            return ini
    raise RuntimeError(
        "alembic.ini not found; expected it next to the backend package or at /app/alembic.ini"
    )


def ensure_schema(db_url: str) -> None:
    ini = _alembic_ini()
    cfg = Config(str(ini))
    cfg.set_main_option("sqlalchemy.url", db_url)
    cfg.set_main_option("script_location", str(ini.parent / "alembic"))
    alembic_command.upgrade(cfg, "head")


def open_session(db_url: str) -> Session:
    connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}
    engine = create_engine(db_url, pool_pre_ping=True, connect_args=connect_args)
    return sessionmaker(bind=engine, expire_on_commit=False)()


def cmd_seed_demo(session: Session, runs: int, project: str, ground_truth: Path) -> dict:
    return seed_demo(session, project=project, runs=runs, ground_truth_path=ground_truth)


def cmd_ingest(
    session: Session,
    xml_path: Path,
    project: str,
    run_number: int,
    branch: str = "main",
    commit_sha: str | None = None,
    workflow_name: str | None = None,
    environment: str | None = None,
) -> dict:
    try:
        with xml_path.open("rb") as report:
            raw = report.read(MAX_JUNIT_BYTES + 1)
        parsed = parse_junit(raw)
    except JUnitParseError as exc:
        raise RuntimeError(f"invalid JUnit file: {exc}") from exc
    summary = persist_run(
        session,
        TestRunResult(
            project=project,
            run_number=run_number,
            branch=branch,
            commit_sha=commit_sha,
            workflow_name=workflow_name,
            environment=environment,
            cases=parsed.cases,
        ),
    )
    return {
        "run_id": summary.run_id,
        "project": summary.project,
        "run_number": summary.run_number,
        "summary": {
            "total": summary.total,
            "passed": summary.passed,
            "failed": summary.failed,
            "error": summary.error,
            "skipped": summary.skipped,
            "new_tests": summary.new_tests,
            "duplicates": summary.duplicates,
        },
    }


def _scope_case_ids(session: Session, project: str | None) -> tuple[list[int], str]:
    if project is None:
        ids = session.scalars(select(TestCase.id).order_by(TestCase.id)).all()
        return list(ids), "all projects"
    row = session.scalar(select(Project).where(Project.name == project))
    if row is None:
        raise RuntimeError(f"project '{project}' not found")
    ids = session.scalars(
        select(TestCase.id).where(TestCase.project_id == row.id).order_by(TestCase.id)
    ).all()
    return list(ids), project


def cmd_analyze(
    session: Session,
    project: str | None,
    ground_truth: Path | None,
    config: AnalysisConfig | None = None,
) -> dict:
    config = config or AnalysisConfig.from_settings(get_settings())
    case_ids, scope = _scope_case_ids(session, project)
    analyses = [analyze_test_case(session, cid, config) for cid in case_ids]
    predicted = {
        a.unique_key: (a.classification in FLAKY_CLASSIFICATIONS or a.newly_flaky) for a in analyses
    }
    eval_result = None
    if ground_truth is not None and ground_truth.exists():
        truth = json.loads(ground_truth.read_text())
        eval_result = evaluate(predicted, truth)
    return {"scope": scope, "analyses": analyses, "eval": eval_result}


def cmd_list_flaky(
    session: Session,
    project: str | None,
    min_score: float | None,
    limit: int,
    config: AnalysisConfig | None = None,
) -> list:
    config = config or AnalysisConfig.from_settings(get_settings())
    case_ids, _ = _scope_case_ids(session, project)
    threshold = config.flaky_threshold if min_score is None else min_score
    analyses = [analyze_test_case(session, cid, config) for cid in case_ids]
    # Newly-flaky tests bypass the score gate: their recent window already
    # classified flaky at threshold; the overall score lags by construction.
    flagged = [
        a
        for a in analyses
        if a.newly_flaky
        or (a.classification in FLAKY_CLASSIFICATIONS and a.flakiness_score >= threshold)
    ]
    flagged.sort(key=lambda a: a.flakiness_score, reverse=True)
    return flagged[:limit]


def _print_analyses(analyses: list, limit: int = 50) -> None:
    print(f"{'TEST':60s} {'CLASS':20s} {'SCORE':>6s} {'PASS%':>6s} {'N':>4s}")
    for a in analyses[:limit]:
        name = a.unique_key[-60:]
        print(
            f"{name:60s} {a.classification:20s} {a.flakiness_score:6.2f} "
            f"{a.pass_rate * 100:5.1f}% {a.sample_size:4d}"
        )
    if len(analyses) > limit:
        print(f"... and {len(analyses) - limit} more")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="flakyctl", description="Flaky Test Intelligence CLI")
    parser.add_argument("--db-url", default=None, help="Database URL (default: DATABASE_URL env)")
    sub = parser.add_subparsers(dest="command", required=True)

    seed = sub.add_parser("seed-demo", help="Seed deterministic demo history")
    seed.add_argument(
        "--runs", type=int, default=DEFAULT_RUNS, help=f"CI runs ({MIN_RUNS}-{MAX_RUNS})"
    )
    seed.add_argument("--project", default=DEFAULT_PROJECT)
    seed.add_argument("--ground-truth", default="demo/ground_truth.json")

    ingest = sub.add_parser("ingest", help="Ingest one JUnit XML file")
    ingest.add_argument("xml", type=Path)
    ingest.add_argument("--project", required=True)
    ingest.add_argument("--run-number", type=int, required=True)
    ingest.add_argument("--branch", default="main")
    ingest.add_argument("--commit-sha", default=None)
    ingest.add_argument("--workflow", default=None)
    ingest.add_argument("--environment", default=None)

    analyze = sub.add_parser("analyze", help="Analyze tests and print classifications")
    analyze.add_argument("--project", default=None)
    analyze.add_argument("--ground-truth", default="demo/ground_truth.json")

    flaky = sub.add_parser("list-flaky", help="List flaky tests by score")
    flaky.add_argument("--project", default=None)
    flaky.add_argument("--min-score", type=float, default=None)
    flaky.add_argument("--limit", type=int, default=20)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    db_url = resolve_db_url(args.db_url)
    try:
        ensure_schema(db_url)
        session = open_session(db_url)
        try:
            if args.command == "seed-demo":
                summary = cmd_seed_demo(session, args.runs, args.project, Path(args.ground_truth))
                print(
                    f"seeded {summary['runs']} runs x {summary['tests']} tests "
                    f"for project '{summary['project']}'"
                )
                print(f"ground truth: {summary['ground_truth_path']}")
            elif args.command == "ingest":
                try:
                    result = cmd_ingest(
                        session,
                        args.xml,
                        args.project,
                        args.run_number,
                        args.branch,
                        args.commit_sha,
                        args.workflow,
                        args.environment,
                    )
                except DuplicateRunError as exc:
                    print(f"error: {exc}", file=sys.stderr)
                    return 1
                print(json.dumps(result, indent=2))
            elif args.command == "analyze":
                gt = Path(args.ground_truth)
                result = cmd_analyze(session, args.project, gt if gt.exists() else None)
                print(f"scope: {result['scope']} ({len(result['analyses'])} tests)")
                _print_analyses(result["analyses"])
                if result["eval"] is not None:
                    e = result["eval"]
                    print(
                        f"eval: TP={e.true_positives} TN={e.true_negatives} "
                        f"FP={e.false_positives} FN={e.false_negatives} "
                        f"precision={e.precision:.3f} recall={e.recall:.3f}"
                    )
            elif args.command == "list-flaky":
                flagged = cmd_list_flaky(session, args.project, args.min_score, args.limit)
                print(f"{len(flagged)} flaky test(s):")
                _print_analyses(flagged, limit=args.limit)
        finally:
            session.close()
    except (RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
