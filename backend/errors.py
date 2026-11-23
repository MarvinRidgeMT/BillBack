"""API errors with a stable `code` the front end translates (frontend/messages/*.json "err.<code>").

Body: {"success": false, "data": null, "error": <English message>, "code": <code>, "detail": <same message>}.
`detail` stays for older clients that read FastAPI's default shape. Messages never include bill values.
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

# code -> HTTP status
CODES: dict[str, int] = {
    "bad_file": 400,
    "too_large": 413,
    "invalid_input": 422,
    "not_found": 404,
    "live_off": 403,
    "demo_only": 409,
    "bad_url": 400,
    "fetch_failed": 502,
    "fetch_timeout": 504,
    "not_pdf": 422,
    "no_pdf_link": 422,
    "pdf_encrypted": 422,
    "pdf_empty": 422,
    "too_short": 422,
    "ai_unavailable": 503,
    "ai_invalid": 502,
    "server_error": 500,
}


class AppError(Exception):
    def __init__(self, code: str, message: str, status: int | None = None, extra: dict[str, Any] | None = None):
        if code not in CODES:
            raise ValueError(f"unknown error code {code!r}")
        super().__init__(message)
        self.code, self.message = code, message
        self.status = status or CODES[code]
        self.extra = extra or {}


def error_body(code: str, message: str, **extra: Any) -> dict[str, Any]:
    return {"success": False, "data": None, "error": message, "code": code, "detail": message, **extra}


def install(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(error_body(exc.code, exc.message, **exc.extra), status_code=exc.status)

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        fields = sorted({str(e["loc"][-1]) for e in exc.errors() if e.get("loc")})
        body = error_body("invalid_input", "Some answers are missing or out of range: " + ", ".join(fields), fields=fields)
        body["detail"] = exc.errors()  # FastAPI's default list, unchanged for old clients
        return JSONResponse(body, status_code=422)

    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = {400: "bad_file", 403: "live_off", 404: "not_found", 409: "demo_only", 413: "too_large",
                503: "ai_unavailable"}.get(exc.status_code, "server_error")
        return JSONResponse(error_body(code, str(exc.detail)), status_code=exc.status_code)
