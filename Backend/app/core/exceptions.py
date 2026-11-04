from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class ConflictError(Exception):
    def __init__(self, detail: str) -> None:
        self.detail = detail


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ConflictError)
    async def handle_conflict(
        request: Request,
        exc: ConflictError,
    ) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": exc.detail})

