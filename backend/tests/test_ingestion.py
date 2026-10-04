"""Phase 3 tests: parser, identity, persistence service, upload API."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.ingestion.identity import build_unique_key
from app.ingestion.parser import JUnitParseError, parse_junit
from app.ingestion.schemas import TestCaseResult, TestRunResult
from app.ingestion.service import DuplicateRunError, persist_run
from app.main import create_app
from app.models import Project, TestCase, TestExecution, TestRun

TestRunResult.__test__ = False  # pydantic schema, not a test class

SINGLE_SUITE = b"""<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="auth" tests="4">
  <testcase classname="tests.test_auth" name="test_valid_login" time="0.12"/>
  <testcase classname="tests.test_auth" name="test_expired_token" time="0.34">
    <failure type="AssertionError" message="expected 200">assert status == 200</failure>
  </testcase>
  <testcase classname="tests.test_auth" name="test_db_unavailable" time="1.02">
    <error type="ConnectionError">could not connect</error>
  </testcase>
  <testcase classname="tests.test_auth" name="test_sso" time="0.0">
    <skipped/>
  </testcase>
</testsuite>
"""

MULTI_SUITE = b"""<?xml version="1.0" encoding="UTF-8"?>
<testsuites>
  <testsuite name="auth"><testcase classname="a" name="t1" time="0.1"/></testsuite>
  <testsuite name="billing"><testcase classname="b" name="t2" time="0.2"/></testsuite>
</testsuites>
"""

XXE_XML = (
    b'<?xml version="1.0"?>'
    b'<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>'
    b'<testsuite><testcase classname="a" name="t">&xxe;</testcase></testsuite>'
)

EXPANSION_XML = (
    b'<?xml version="1.0"?>'
    b'<!DOCTYPE lolz [<!ENTITY lol "lollollollollollollollol">'
    b'<!ENTITY lol2 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">]>'
    b'<testsuite><testcase classname="a" name="t">&lol2;</testcase></testsuite>'
)


def test_parse_single_suite_statuses():
    parsed = parse_junit(SINGLE_SUITE)
    by_name = {c.test_name: c for c in parsed.cases}
    assert by_name["test_valid_login"].status == "passed"
    assert by_name["test_expired_token"].status == "failed"
    assert by_name["test_expired_token"].failure_type == "AssertionError"
    assert "assert status == 200" in (by_name["test_expired_token"].failure_message or "")
    assert by_name["test_db_unavailable"].status == "error"
    assert by_name["test_sso"].status == "skipped"
    assert by_name["test_valid_login"].duration == pytest.approx(0.12)
    assert all(c.suite_name == "auth" for c in parsed.cases)


def test_parse_multiple_suites():
    parsed = parse_junit(MULTI_SUITE)
    assert len(parsed.cases) == 2
    assert {c.suite_name for c in parsed.cases} == {"auth", "billing"}


def test_parse_rejects_malformed_xml():
    with pytest.raises(JUnitParseError, match="malformed"):
        parse_junit(b"<testsuite><broken")


def test_parse_rejects_xxe_and_entity_expansion():
    with pytest.raises(JUnitParseError, match="unsafe"):
        parse_junit(XXE_XML)
    with pytest.raises(JUnitParseError, match="unsafe"):
        parse_junit(EXPANSION_XML)


def test_parse_rejects_empty_and_caseless_files():
    with pytest.raises(JUnitParseError, match="empty"):
        parse_junit(b"   ")
    with pytest.raises(JUnitParseError, match="no test cases"):
        parse_junit(b"<testsuites></testsuites>")
    with pytest.raises(JUnitParseError, match="unsupported root"):
        parse_junit(b"<coverage></coverage>")


def test_parse_rejects_missing_test_name():
    with pytest.raises(JUnitParseError, match="missing required 'name'"):
        parse_junit(b'<testsuite name="s"><testcase classname="a" time="0.1"/></testsuite>')


def test_parse_tolerates_missing_or_invalid_duration():
    parsed = parse_junit(
        b'<testsuite name="s">'
        b'<testcase classname="a" name="t1"/>'
        b'<testcase classname="a" name="t2" time="nan"/>'
        b"</testsuite>"
    )
    assert [c.duration for c in parsed.cases] == [0.0, 0.0]


def test_parse_classname_falls_back_to_suite():
    parsed = parse_junit(b'<testsuite name="s"><testcase name="t" time="0.1"/></testsuite>')
    assert parsed.cases[0].classname == "s"


def test_identity_rules():
    assert build_unique_key("p", "a.B", "t") == "p::a.B::t"
    assert build_unique_key("p", "a.B", "t") == build_unique_key("p", "a.B", "t")
    assert build_unique_key("p", "a.B", "t1") != build_unique_key("p", "a.B", "t2")


def test_run_result_rejects_identity_that_exceeds_database_limit():
    project = "p" * 255
    classname = "c" * 1024
    at_limit = TestCaseResult(
        classname=classname,
        test_name="t" * 765,
        status="passed",
    )
    TestRunResult(project=project, run_number=1, cases=[at_limit])

    too_long = TestCaseResult(
        classname=classname,
        test_name="t" * 766,
        status="passed",
    )
    with pytest.raises(ValidationError, match="2048-character limit"):
        TestRunResult(project=project, run_number=2, cases=[too_long])


def _run_result(**overrides) -> TestRunResult:
    parsed = parse_junit(SINGLE_SUITE)
    base: dict = {"project": "demo-project", "run_number": 1, "cases": parsed.cases}
    base.update(overrides)
    return TestRunResult(**base)


def test_persist_run_creates_history(db_session):
    summary = persist_run(db_session, _run_result())
    assert (summary.total, summary.passed, summary.failed) == (4, 1, 1)
    assert (summary.error, summary.skipped) == (1, 1)
    assert summary.new_tests == 4 and summary.duplicates == 0

    run = db_session.scalar(select(TestRun).where(TestRun.id == summary.run_id))
    assert (run.total_tests, run.passed_tests, run.failed_tests) == (4, 1, 1)
    case = db_session.scalar(
        select(TestCase).where(
            TestCase.unique_key == "demo-project::tests.test_auth::test_valid_login"
        )
    )
    assert case is not None and len(case.executions) == 1


def test_persist_run_dedupes_and_reuses_cases(db_session):
    parsed = parse_junit(SINGLE_SUITE)
    cases = list(parsed.cases) + [parsed.cases[0]]
    summary = persist_run(
        db_session, TestRunResult(project="demo-project", run_number=1, cases=cases)
    )
    assert summary.duplicates == 1 and summary.total == 4

    summary2 = persist_run(db_session, _run_result(run_number=2))
    assert summary2.new_tests == 0
    assert db_session.scalar(select(func.count()).select_from(TestCase)) == 4
    assert db_session.scalar(select(func.count()).select_from(TestExecution)) == 8


def test_persist_run_rejects_duplicate_run(db_session):
    persist_run(db_session, _run_result())
    with pytest.raises(DuplicateRunError):
        persist_run(db_session, _run_result())
    assert db_session.scalar(select(func.count()).select_from(TestRun)) == 1


def test_persist_run_rejects_conflicting_duplicates(db_session):
    from app.ingestion.service import ConflictingDuplicateTestError

    parsed = parse_junit(SINGLE_SUITE)
    altered = parsed.cases[0].model_copy(update={"status": "failed"})
    with pytest.raises(ConflictingDuplicateTestError):
        persist_run(
            db_session,
            TestRunResult(project="demo-project", run_number=1, cases=[parsed.cases[0], altered]),
        )


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)

    def override():
        session = factory()
        try:
            yield session
        finally:
            session.close()

    app = create_app()
    app.dependency_overrides[get_db] = override
    return TestClient(app)


def _upload(client: TestClient, payload: bytes, filename: str = "results.xml", **data):
    fields = {"project": "demo-project", "run_number": "3", "branch": "main"}
    fields.update(data)
    return client.post(
        "/api/runs/upload",
        files={"file": (filename, payload, "text/xml")},
        data=fields,
    )


def test_upload_happy_path(client):
    response = _upload(client, SINGLE_SUITE)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["project"] == "demo-project" and body["run_number"] == 3
    assert body["summary"] == {
        "total": 4,
        "passed": 1,
        "failed": 1,
        "error": 1,
        "skipped": 1,
        "new_tests": 4,
        "duplicates": 0,
    }


def test_upload_rejects_duplicate_run(client):
    assert _upload(client, SINGLE_SUITE).status_code == 201
    response = _upload(client, SINGLE_SUITE)
    assert response.status_code == 409
    assert response.json()["error"] == "DUPLICATE_RUN"
    assert "request_id" in response.json()


def test_upload_rejects_bad_xml_and_wrong_type(client):
    bad = _upload(client, b"<nope><broken", run_number="10")
    assert bad.status_code == 400
    assert bad.json()["error"] == "INVALID_JUNIT_FILE"

    wrong_type = _upload(client, SINGLE_SUITE, filename="results.json", run_number="11")
    assert wrong_type.status_code == 400
    assert wrong_type.json()["error"] == "INVALID_FILE_TYPE"


def test_upload_rejects_empty_file(client):
    response = _upload(client, b"", run_number="12")
    assert response.status_code == 400
    assert response.json()["error"] == "INVALID_JUNIT_FILE"


def test_upload_rejects_conflicting_duplicate_records(client):
    xml = (
        b'<testsuite name="s">'
        b'<testcase classname="a" name="t" time="0.1"/>'
        b'<testcase classname="a" name="t" time="0.1"><failure>boom</failure></testcase>'
        b"</testsuite>"
    )
    response = _upload(client, xml, run_number="30")
    assert response.status_code == 400
    assert response.json()["error"] == "CONFLICTING_TEST_RECORDS"


def test_upload_rejects_oversized_file(client):
    big = b"<testsuite>" + b"<testcase classname='a' name='t' time='0.1'/>" * 200_000
    big += b"</testsuite>"
    assert len(big) > 5 * 1024 * 1024
    response = _upload(client, big, run_number="13")
    assert response.status_code == 413
    assert response.json()["error"] == "FILE_TOO_LARGE"


def test_upload_rejects_missing_project(client):
    response = client.post(
        "/api/runs/upload",
        files={"file": ("results.xml", SINGLE_SUITE, "text/xml")},
        data={"run_number": "14"},
    )
    assert response.status_code == 422
    assert response.json()["error"] == "VALIDATION_ERROR"


def test_upload_rejects_missing_run_number(client):
    response = client.post(
        "/api/runs/upload",
        files={"file": ("results.xml", SINGLE_SUITE, "text/xml")},
        data={"project": "sec"},
    )
    assert response.status_code == 422
    assert response.json()["error"] == "VALIDATION_ERROR"
    assert "request_id" in response.json()


def test_upload_persists_queryable_history(client):
    _upload(client, SINGLE_SUITE, run_number="21")
    _upload(client, SINGLE_SUITE, run_number="22")
    assert (
        client.post(
            "/api/runs/upload",
            files={"file": ("r.xml", SINGLE_SUITE, "text/xml")},
            data={"project": "demo-project", "run_number": "21"},
        ).status_code
        == 409
    )
    assert Project is not None  # models import sanity for coverage
