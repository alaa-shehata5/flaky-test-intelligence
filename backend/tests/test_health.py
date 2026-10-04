"""Phase 1 smoke tests: health endpoint + configuration defaults."""

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import create_app


def test_health_returns_ok():
    client = TestClient(create_app())
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert "X-Request-ID" in response.headers


def test_config_defaults():
    settings = get_settings()
    assert settings.min_sample_size == 5
    assert settings.flaky_score_threshold == 40.0
    assert settings.highly_flaky_score_threshold == 70.0
    assert settings.slow_test_threshold == 5.0
    assert isinstance(settings.cors_origins, list)
