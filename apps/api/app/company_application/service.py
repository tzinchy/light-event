import secrets
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.company.models import CompanyStatus
from app.company.repo import CompanyRepo
from app.company_application.models import ApplicationStatus, CompanyApplication
from app.company_application.repo import CompanyApplicationRepo
from app.company_application.schemas import AdminApplicationOut, ApplicationSubmitIn
from app.core.errors import DomainError
from app.core.storage import Storage
from app.document.service import ALLOWED_MIMES
from app.team.models import CompanyRole
from app.team.repo import TeamRepo
from app.user.models import ModerationStatus, User
from app.user.repo import UserRepo

_COMPANY_FIELDS = (
    "name",
    "description",
    "inn",
    "ogrn",
    "address",
    "lat",
    "lon",
    "contact_phone",
    "contact_name",
    "contact_email",
    "contact_position",
)


class PublicApplicationService:
    """Публичный приём заявок на отель — без учётной записи (PLAN §11.16)."""

    def __init__(self, session: AsyncSession, storage: Storage, max_size_mb: int):
        self.session = session
        self.storage = storage
        self.max_size_mb = max_size_mb
        self.repo = CompanyApplicationRepo(session)

    async def submit(self, data: ApplicationSubmitIn) -> CompanyApplication:
        return await self.repo.create(**data.model_dump(), upload_token=secrets.token_urlsafe(32))

    async def attach_document(self, application_uuid: UUID, token: str, content: bytes, mime: str) -> None:
        application = await self.repo.get(application_uuid)
        if application is None:
            raise DomainError(404, "Заявка не найдена")
        if not secrets.compare_digest(application.upload_token, token):
            raise DomainError(403, "Неверный токен загрузки")
        if mime not in ALLOWED_MIMES:
            raise DomainError(415, "Неподдерживаемый формат файла (нужен JPEG/PNG/WebP/PDF)")
        if not content:
            raise DomainError(422, "Пустой файл")
        if len(content) > self.max_size_mb * 1024 * 1024:
            raise DomainError(413, f"Файл больше {self.max_size_mb} МБ")
        key = f"applications/{application_uuid}/proof"
        await self.storage.put(key, content, mime)
        application.proof_storage_key = key
        application.proof_mime = mime
        await self.session.flush()


class AdminApplicationService:
    """Модерация заявок админом: список, пруф, approve (заводит компанию+владельца), reject."""

    def __init__(self, session: AsyncSession, storage: Storage):
        self.session = session
        self.storage = storage
        self.repo = CompanyApplicationRepo(session)

    async def _get(self, application_uuid: UUID) -> CompanyApplication:
        application = await self.repo.get(application_uuid)
        if application is None:
            raise DomainError(404, "Заявка не найдена")
        return application

    async def list_by_status(self, status: ApplicationStatus) -> list[AdminApplicationOut]:
        return [
            AdminApplicationOut.model_validate(a).model_copy(
                update={"has_document": a.proof_storage_key is not None}
            )
            for a in await self.repo.list_by_status(status)
        ]

    async def proof_content(self, application_uuid: UUID) -> tuple[bytes, str]:
        application = await self._get(application_uuid)
        if application.proof_storage_key is None:
            raise DomainError(404, "Документ не приложен")
        data = await self.storage.get(application.proof_storage_key)
        return data, application.proof_mime or "application/octet-stream"

    async def approve(self, application_uuid: UUID) -> CompanyApplication:
        application = await self._get(application_uuid)
        if application.status == ApplicationStatus.approved:
            raise DomainError(409, "Заявка уже одобрена")

        company = await CompanyRepo(self.session).create(
            **{f: getattr(application, f) for f in _COMPANY_FIELDS},
            status=CompanyStatus.verified,
            verified_at=datetime.now(timezone.utc),
        )
        # заявитель становится владельцем кабинета: находим или заводим пользователя по контактной почте
        users = UserRepo(self.session)
        owner = await users.get_by_email(application.contact_email)
        if owner is None:
            owner = await users.create_with_email(application.contact_email)
            owner.name = application.contact_name
            owner.moderation_status = ModerationStatus.approved
        await TeamRepo(self.session).add_member(
            company_uuid=company.company_uuid,
            user_uuid=owner.user_uuid,
            role=CompanyRole.main_manager,
            perm_create=True,
            perm_hire=True,
            perm_finance=True,
            perm_invite=True,
        )
        application.status = ApplicationStatus.approved
        application.company_uuid = company.company_uuid
        application.reviewed_at = datetime.now(timezone.utc)
        await self.session.flush()
        # ponytail: письмо-приглашение заявителю (OTP уже работает по этой почте) — добавить при интеграции web
        return application

    async def reject(self, application_uuid: UUID, reason: str) -> CompanyApplication:
        application = await self._get(application_uuid)
        application.status = ApplicationStatus.rejected
        application.reject_reason = reason
        application.reviewed_at = datetime.now(timezone.utc)
        await self.session.flush()
        return application
