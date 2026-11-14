"""Errores con el formato del contrato: {"error": "codigo_corto", "detail": "texto"}."""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class ApiError(Exception):
    def __init__(self, status: int, error: str, detail: str) -> None:
        self.status, self.error, self.detail = status, error, detail


def not_found(what: str, ident: str) -> ApiError:
    return ApiError(404, f"{what}_not_found", f"No existe {what} '{ident}'.")


def install(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def _api(_: Request, e: ApiError):
        return JSONResponse({"error": e.error, "detail": e.detail}, status_code=e.status)

    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, e: StarletteHTTPException):
        code = {404: "not_found", 405: "method_not_allowed"}.get(e.status_code, "http_error")
        return JSONResponse({"error": code, "detail": str(e.detail)}, status_code=e.status_code)

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, e: RequestValidationError):
        msgs = "; ".join(f"{'.'.join(map(str, err['loc']))}: {err['msg']}" for err in e.errors())
        return JSONResponse({"error": "invalid_request", "detail": msgs}, status_code=422)
