from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.complaint.models import Complaint, ComplaintStatus
from app.complaint.repo import ComplaintRepo
from app.complaint.schemas import ComplaintCreateIn, ComplaintResolveIn
from app.core.errors import DomainError
from app.user.models import User


class ComplaintService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = ComplaintRepo(session)

    async def create(self, actor: User, data: ComplaintCreateIn) -> Complaint:
        complaint = Complaint(
            author_uuid=actor.user_uuid,
            target_type=data.target_type,
            target_uuid=data.target_uuid,
            vacancy_uuid=data.vacancy_uuid,
            kind=data.kind,
            severity=data.severity,
            text=data.text,
        )
        self.repo.add(complaint)
        await self.session.flush()
        return complaint

    async def list_my(self, actor: User) -> list[Complaint]:
        return await self.repo.list_by_author(actor.user_uuid)

    async def list_open(self) -> list[Complaint]:
        return await self.repo.list_open()

    async def resolve(self, admin: User, complaint_uuid: UUID, data: ComplaintResolveIn) -> Complaint:
        complaint = await self.repo.get_for_update(complaint_uuid)
        if complaint is None:
            raise DomainError(404, "Жалоба не найдена")
        if complaint.status != ComplaintStatus.open:
            raise DomainError(409, "Жалоба уже рассмотрена")
        complaint.status = ComplaintStatus(data.action)
        complaint.resolution = data.resolution
        complaint.resolved_by_uuid = admin.user_uuid
        complaint.resolved_at = datetime.now(UTC)
        await self.session.flush()
        return complaint
