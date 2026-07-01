"""Shared response envelope schemas.

Every endpoint returns { success, data, error, meta } so the client parses one
shape regardless of success or failure.
"""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Meta(BaseModel):
    request_id: str
    cached: bool = False
    source: str | None = None


class ErrorInfo(BaseModel):
    error_code: str
    message: str


class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T | None = None
    error: ErrorInfo | None = None
    meta: Meta
