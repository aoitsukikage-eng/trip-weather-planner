"""Typed application errors and FastAPI exception handlers.

All error responses share the same envelope as success responses
(success / data / error / meta) so the frontend has one contract to parse.
"""

from __future__ import annotations

import uuid

from fastapi import Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    """Base class for expected, client-facing errors."""

    status_code = 400
    error_code = "bad_request"

    def __init__(self, message: str, *, error_code: str | None = None,
                 status_code: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        if error_code is not None:
            self.error_code = error_code
        if status_code is not None:
            self.status_code = status_code


class UpstreamError(AppError):
    status_code = 502
    error_code = "upstream_error"


class NotFoundError(AppError):
    status_code = 404
    error_code = "not_found"


def _envelope(error_code: str, message: str, request_id: str) -> dict:
    return {
        "success": False,
        "data": None,
        "error": {"error_code": error_code, "message": message},
        "meta": {"request_id": request_id},
    }


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    return JSONResponse(
        status_code=exc.status_code,
        content=_envelope(exc.error_code, exc.message, request_id),
    )


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    # Do not leak internal details to the client.
    return JSONResponse(
        status_code=500,
        content=_envelope("internal_error", "An unexpected error occurred.", request_id),
    )
