from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.errors import DomainError
from app.core.storage import Storage
from app.document.models import Document, DocumentKind
from app.document.repo import DocumentRepo
from app.user.models import PlatformRole, User

ALLOWED_MIMES = {"image/jpeg", "image/png", "image/webp", "application/pdf"}


class DocumentService:
    def __init__(self, session: AsyncSession, storage: Storage, settings: Settings):
        self.session = session
        self.storage = storage
        self.settings = settings
        self.docs = DocumentRepo(session)

    async def upload(self, user: User, kind: DocumentKind, content: bytes, mime: str) -> Document:
        if mime not in ALLOWED_MIMES:
            raise DomainError(415, "Неподдерживаемый формат файла (нужен JPEG/PNG/WebP/PDF)")
        if not content:
            raise DomainError(422, "Пустой файл")
        if len(content) > self.settings.document_max_size_mb * 1024 * 1024:
            raise DomainError(413, f"Файл больше {self.settings.document_max_size_mb} МБ")

        doc = await self.docs.create(
            owner_uuid=user.user_uuid,
            kind=kind,
            storage_key="",  # ключ включает document_uuid, поэтому проставляется после flush
            mime=mime,
            size_bytes=len(content),
        )
        doc.storage_key = f"documents/{user.user_uuid}/{doc.document_uuid}"
        await self.storage.put(doc.storage_key, content, mime)
        return doc

    async def list_my(self, user: User) -> list[Document]:
        return await self.docs.list_by_owner(user.user_uuid)

    async def get_content(self, user: User, document_uuid: UUID) -> tuple[bytes, str]:
        doc = await self.docs.get(document_uuid)
        if doc is None:
            raise DomainError(404, "Документ не найден")
        is_owner = doc.owner_uuid == user.user_uuid
        is_admin = user.platform_role == PlatformRole.admin
        if not (is_owner or is_admin):
            # компания/работодатель содержимое KYC не получает никогда (skill s3-documents-kyc)
            raise DomainError(403, "Нет доступа к содержимому документа")
        data = await self.storage.get(doc.storage_key)
        return data, doc.mime
