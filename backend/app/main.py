"""FastAPI application entrypoint."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.config import get_settings
from app.core.logging import clear_request_id, get_logger, set_request_id, setup_logging

logger = get_logger(__name__)


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        incoming = request.headers.get("X-Request-ID")
        rid = set_request_id(incoming)
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = rid
            return response
        finally:
            clear_request_id()


def create_app() -> FastAPI:
    settings = get_settings()
    setup_logging(settings.log_level)

    application = FastAPI(title="Flaky Test Intelligence Platform")
    application.add_middleware(RequestIdMiddleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.get("/health")
    def health() -> dict[str, str]:
        logger.info("health check")
        return {"status": "ok"}

    return application


app = create_app()
