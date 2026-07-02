from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.document.models import Document, DocumentKind


class DocumentRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, document_uuid: UUID) -> Document | None:
        return await self.session.get(Document, document_uuid)

    async def list_by_owner(self, owner_uuid: UUID) -> list[Document]:
        result = await self.session.execute(
            select(Document).where(Document.owner_uuid == owner_uuid).order_by(Document.document_uuid)
        )
        return list(result.scalars())

    async def create(self, owner_uuid: UUID, kind: DocumentKind, storage_key: str, mime: str, size_bytes: int) -> Document:
        doc = Document(
            owner_uuid=owner_uuid, kind=kind, storage_key=storage_key, mime=mime, size_bytes=size_bytes
        )
        self.session.add(doc)
        await self.session.flush()
        return doc
