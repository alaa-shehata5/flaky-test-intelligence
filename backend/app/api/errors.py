"""Consistent API error envelope: {"error", "message", "request_id"}."""

from __future__ import annotations

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.logging import get_logger, get_request_id

logger = get_logger(__name__)


class ApiError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


def _payload(code: str, message: str) -> dict[str, str]:
    return {"error": code, "message": message, "request_id": get_request_id()}


async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
    logger.warning("api error %s: %s", exc.code, exc.message)
    return JSONResponse(status_code=exc.status_code, content=_payload(exc.code, exc.message))


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    logger.warning("validation error: %s", exc.errors())
    return JSONResponse(
        status_code=422,
        content=_payload("VALIDATION_ERROR", "Request validation failed."),
    )


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled error")
    return JSONResponse(
        status_code=500,
        content=_payload("INTERNAL_ERROR", "An unexpected error occurred."),
    )


def register_error_handlers(app) -> None:
    app.add_exception_handler(ApiError, api_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_error_handler)
