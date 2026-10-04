"""Phase 6 tests: projects, runs, tests, flaky-tests, history, summary APIs."""

from __future__ import annotations

from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.ingestion.schemas import TestCaseResult, TestRunResult
from app.ingestion.service import persist_run
from app.main import create_app


def _cases(statuses: dict[str, str]) -> list[TestCaseResult]:
    return [
        TestCaseResult(
            suite_name="s",
            classname="c.T",
            test_name=name,
            status=status,  # type: ignore[arg-type]
            duration=0.5,
        )
        for name, status in statuses.items()
    ]


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    session = factory()
    for run_number in range(1, 7):
        persist_run(
            session,
            TestRunResult(
                project="api-p1",
                run_number=run_number,
                branch="main",
                cases=_cases(
                    {
                        "t_stable": "passed",
                        "t_flaky": "passed" if run_number % 2 else "failed",
                        "t_broken": "failed",
                    }
                ),
            ),
        )
    persist_run(
        session,
        TestRunResult(
            project="api-p1",
            run_number=7,
            branch="dev",
            cases=_cases({"t_stable": "passed", "t_flaky": "passed", "t_broken": "passed"}),
        ),
    )
    persist_run(
        session,
        TestRunResult(
            project="api-p2",
            run_number=1,
            cases=_cases({"t_other": "passed"}),
        ),
    )
    session.close()

    def override():
        session = factory()
        try:
            yield session
        finally:
            session.close()

    app = create_app()
    app.dependency_overrides[get_db] = override
    return TestClient(app)


def _project_id(client: TestClient, name: str) -> int:
    for item in client.get("/api/projects").json()["items"]:
        if item["name"] == name:
            return item["id"]
    raise AssertionError(f"project {name} missing")


def test_projects_crud(client: TestClient):
    listed = client.get("/api/projects").json()
    assert listed["total"] == 2
    assert listed["items"][0]["test_count"] == 3

    created = client.post("/api/projects", json={"name": "api-p3"}).json()
    assert created["run_count"] == 0 and created["test_count"] == 0

    dup = client.post("/api/projects", json={"name": "api-p3"})
    assert dup.status_code == 409
    assert dup.json()["error"] == "PROJECT_EXISTS"

    blank = client.post("/api/projects", json={"name": "   "})
    assert blank.status_code == 400

    one = client.get(f"/api/projects/{created['id']}").json()
    assert one["name"] == "api-p3"

    missing = client.get("/api/projects/9999")
    assert missing.status_code == 404
    body = missing.json()
    assert body["error"] == "PROJECT_NOT_FOUND"
    assert "request_id" in body


def test_runs_list_pagination_and_filters(client: TestClient):
    p1 = _project_id(client, "api-p1")
    page = client.get("/api/runs", params={"limit": 3, "offset": 0}).json()
    assert page["total"] == 8 and len(page["items"]) == 3
    ids = [i["id"] for i in page["items"]]
    assert ids == sorted(ids, reverse=True)

    scoped = client.get("/api/runs", params={"project_id": p1}).json()
    assert scoped["total"] == 7

    dev = client.get("/api/runs", params={"branch": "dev"}).json()
    assert dev["total"] == 1 and dev["items"][0]["run_number"] == 7

    missing_project = client.get("/api/runs", params={"project_id": 9999})
    assert missing_project.status_code == 404


def test_run_detail_and_404(client: TestClient):
    first_id = client.get("/api/runs", params={"limit": 1}).json()["items"][0]["id"]
    detail = client.get(f"/api/runs/{first_id}").json()
    assert detail["project_name"] == "api-p2"
    assert detail["total_tests"] == 1

    missing = client.get("/api/runs/9999")
    assert missing.status_code == 404
    assert missing.json()["error"] == "RUN_NOT_FOUND"


def _test_id(client: TestClient, project: str, name: str) -> int:
    pid = _project_id(client, project)
    items = client.get("/api/tests", params={"project_id": pid, "limit": 200}).json()["items"]
    for item in items:
        if item["test_name"] == name:
            return item["test_case_id"]
    raise AssertionError(f"{name} missing")


def test_tests_list_and_filters(client: TestClient):
    p1 = _project_id(client, "api-p1")
    flaky = client.get(
        "/api/tests",
        params={"project_id": p1, "branch": "main", "classification": "HIGHLY_FLAKY"},
    ).json()
    assert flaky["total"] == 1
    assert flaky["items"][0]["test_name"] == "t_flaky"
    assert flaky["items"][0]["flakiness_score"] >= 70.0
    assert flaky["items"][0]["failure_rate"] == 0.5
    assert "pass_rate_delta" in flaky["items"][0]
    assert "score_delta" in flaky["items"][0]

    suite = client.get("/api/tests", params={"project_id": p1, "suite": "s"}).json()
    assert suite["total"] == 3

    scored = client.get(
        "/api/tests", params={"project_id": p1, "branch": "main", "minimum_score": 70}
    ).json()
    assert scored["total"] == 1

    searched = client.get("/api/tests", params={"q": "BROKEN"}).json()
    assert searched["total"] == 1

    page = client.get("/api/tests", params={"project_id": p1, "limit": 2, "offset": 1}).json()
    assert page["total"] == 3 and len(page["items"]) == 2

    bad_class = client.get("/api/tests", params={"classification": "NOPE"})
    assert bad_class.status_code == 422
    assert bad_class.json()["error"] == "VALIDATION_ERROR"

    bad_score = client.get("/api/tests", params={"minimum_score": 500})
    assert bad_score.status_code == 422


def test_test_detail_matches_history(client: TestClient):
    tid = _test_id(client, "api-p1", "t_flaky")
    detail = client.get(f"/api/tests/{tid}").json()
    assert detail["sample_size"] == 7
    assert detail["classification"] in ("SUSPECTED_FLAKY", "HIGHLY_FLAKY")

    history = client.get(f"/api/tests/{tid}/history").json()
    assert [h["run_number"] for h in history] == [1, 2, 3, 4, 5, 6, 7]
    assert history[0]["score"] == 0.0
    assert history[-1]["score"] == detail["flakiness_score"]
    assert history[1]["status"] == "failed"
    assert all("executed_at" in h and "duration" in h for h in history)

    missing = client.get("/api/tests/9999")
    assert missing.status_code == 404
    assert missing.json()["error"] == "TEST_NOT_FOUND"
    assert client.get("/api/tests/9999/history").status_code == 404


def test_flaky_tests_ranking(client: TestClient):
    p1 = _project_id(client, "api-p1")
    ranked = client.get("/api/flaky-tests", params={"project_id": p1, "branch": "main"}).json()
    assert ranked["total"] == 1
    assert ranked["items"][0]["test_name"] == "t_flaky"

    by_name = client.get("/api/flaky-tests", params={"sort": "name_asc", "limit": 50}).json()
    names = [i["test_name"] for i in by_name["items"]]
    assert names == sorted(names)

    none_high = client.get("/api/flaky-tests", params={"minimum_score": 99.99}).json()
    assert none_high["total"] == 0 and none_high["items"] == []

    limited = client.get("/api/flaky-tests", params={"limit": 1}).json()
    assert len(limited["items"]) == 1 and limited["total"] >= 1

    bad_sort = client.get("/api/flaky-tests", params={"sort": "nope"})
    assert bad_sort.status_code == 422


def test_dashboard_summary(client: TestClient):
    p1 = _project_id(client, "api-p1")
    summary = client.get(
        "/api/dashboard/summary", params={"project_id": p1, "branch": "main"}
    ).json()
    assert summary["total_tests"] == 3
    assert summary["total_runs"] == 6
    assert summary["stable_tests"] == 1
    assert summary["suspected_flaky_tests"] + summary["highly_flaky_tests"] == 1
    assert summary["consistently_failing_tests"] == 1
    assert summary["slow_tests"] == 0
    assert summary["newly_flaky_tests"] == 0
    assert summary["average_pass_rate"] == pytest.approx((1.0 + 0.5 + 0.0) / 3)

    dev = client.get("/api/dashboard/summary", params={"project_id": p1, "branch": "dev"}).json()
    assert dev["total_runs"] == 1
    assert dev["total_tests"] == 3
    assert dev["average_pass_rate"] == 1.0

    missing = client.get("/api/dashboard/summary", params={"project_id": 9999})
    assert missing.status_code == 404


def test_extended_scope_filters(client: TestClient):
    p1 = _project_id(client, "api-p1")
    scoped = {"project_id": p1, "branch": "main"}

    only_flaky = client.get(
        "/api/dashboard/summary", params={**scoped, "classification": "HIGHLY_FLAKY"}
    ).json()
    assert only_flaky["total_tests"] == 1
    assert only_flaky["highly_flaky_tests"] == 1

    high_bar = client.get(
        "/api/dashboard/summary", params={**scoped, "minimum_score": 99.99}
    ).json()
    assert high_bar["total_tests"] == 0

    by_name = client.get("/api/flaky-tests", params={**scoped, "q": "FLAKY"}).json()
    assert by_name["total"] == 1

    by_workflow = client.get(
        "/api/runs", params={"project_id": p1, "workflow_name": "does-not-exist"}
    ).json()
    assert by_workflow["total"] == 0

    today = date.today().isoformat()
    by_date = client.get("/api/runs", params={"project_id": p1, "date_from": today}).json()
    assert by_date["total"] == 7
