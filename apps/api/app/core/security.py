import time
from uuid import UUID

import jwt

ALGORITHM = "HS256"


def create_access_token(user_uuid: UUID, secret: str, ttl_sec: int) -> str:
    now = int(time.time())
    payload = {"sub": str(user_uuid), "iat": now, "exp": now + ttl_sec, "type": "access"}
    return jwt.encode(payload, secret, algorithm=ALGORITHM)


def decode_access_token(token: str, secret: str) -> UUID:
    """Возвращает user_uuid; бросает jwt.InvalidTokenError на любой невалидный/просроченный токен."""
    payload = jwt.decode(token, secret, algorithms=[ALGORITHM])
    if payload.get("type") != "access":
        raise jwt.InvalidTokenError("не access-токен")
    return UUID(payload["sub"])
