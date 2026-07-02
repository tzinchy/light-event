from uuid import UUID

import uuid_utils


def uuid7() -> UUID:
    """UUIDv7 (сортируемый по времени), генерация на стороне приложения — skill uuid-v7-keys."""
    return UUID(bytes=uuid_utils.uuid7().bytes)
