from fastapi import Request
from fastapi.responses import JSONResponse


class DomainError(Exception):
    """Ошибка доменной логики: сервисы бросают её вместо HTTPException, чтобы не зависеть от FastAPI."""

    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
