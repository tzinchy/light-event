from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.complaint.models import Complaint, ComplaintStatus


class ComplaintRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    def add(self, complaint: Complaint) -> None:
        self.session.add(complaint)

    async def get_for_update(self, complaint_uuid: UUID) -> Complaint | None:
        result = await self.session.execute(
            select(Complaint).where(Complaint.complaint_uuid == complaint_uuid).with_for_update()
        )
        return result.scalar_one_or_none()

    async def list_by_author(self, author_uuid: UUID) -> list[Complaint]:
        result = await self.session.execute(
            select(Complaint)
            .where(Complaint.author_uuid == author_uuid)
            .order_by(Complaint.complaint_uuid.desc())
        )
        return list(result.scalars())

    async def list_open(self) -> list[Complaint]:
        result = await self.session.execute(
            select(Complaint)
            .where(Complaint.status == ComplaintStatus.open)
            .order_by(Complaint.complaint_uuid)
        )
        return list(result.scalars())
