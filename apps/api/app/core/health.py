from fastapi import APIRouter, Request
from sqlalchemy import text

router = APIRouter(tags=["health"])


@router.get("/api/v1/health")
async def health(request: Request) -> dict:
    async with request.app.state.engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    await request.app.state.redis.ping()
    return {"status": "ok", "database": "ok", "redis": "ok"}
