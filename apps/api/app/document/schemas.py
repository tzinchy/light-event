from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class DocumentOut(BaseModel):
    """Метаданные документа. storage_key наружу не отдаётся (skill s3-documents-kyc)."""

    model_config = {"from_attributes": True}

    document_uuid: UUID
    kind: str
    status: str
    mime: str
    size_bytes: int
    reject_reason: str | None
    created_at: datetime
