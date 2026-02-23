from typing import Any

from pydantic import BaseModel


class ApiResponse(BaseModel):
    success: bool
    data: Any = None
    error: str | None = None
    meta: dict | None = None


def ok(data: Any = None, meta: dict | None = None) -> dict:
    return ApiResponse(success=True, data=data, meta=meta).model_dump()


def fail(error: str) -> dict:
    return ApiResponse(success=False, error=error).model_dump()


class PaginationParams(BaseModel):
    page: int = 1
    limit: int = 20

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit
