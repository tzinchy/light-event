"""Агрегаты для admin overview — единственный слой с SQL по чужим таблицам."""

from sqlalchemy import distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.balance.models import LedgerEntry, LedgerKind, Payout, PayoutStatus, TopupRequest, TopupStatus
from app.company.models import Company, CompanyStatus
from app.complaint.models import Complaint, ComplaintStatus
from app.document.models import Document, DocumentStatus
from app.test.models import Test, TestStatus
from app.user.models import User
from app.vacancy.models import Vacancy, VacancyStatus


class AdminOverviewRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _count(self, query) -> int:
        return (await self.session.execute(query)).scalar_one()

    async def users_count(self) -> int:
        return await self._count(select(func.count()).select_from(User))

    async def users_with_verified_docs(self) -> int:
        return await self._count(
            select(func.count(distinct(Document.owner_uuid))).where(
                Document.status == DocumentStatus.verified
            )
        )

    async def turnover_kop(self) -> int:
        result = await self.session.execute(
            select(func.coalesce(func.sum(LedgerEntry.amount_kop), 0)).where(
                LedgerEntry.kind == LedgerKind.topup
            )
        )
        return result.scalar_one()

    async def queue_counts(self) -> dict[str, int]:
        return {
            "companies": await self._count(
                select(func.count()).select_from(Company).where(Company.status == CompanyStatus.pending)
            ),
            "requests": (
                await self._count(
                    select(func.count())
                    .select_from(Vacancy)
                    .where(Vacancy.status == VacancyStatus.pending_moderation)
                )
                + await self._count(
                    select(func.count()).select_from(Test).where(Test.status == TestStatus.pending_moderation)
                )
            ),
            "topups": await self._count(
                select(func.count())
                .select_from(TopupRequest)
                .where(TopupRequest.status == TopupStatus.pending)
            ),
            "payouts": await self._count(
                select(func.count()).select_from(Payout).where(Payout.status == PayoutStatus.pending)
            ),
            "kyc": await self._count(
                select(func.count()).select_from(Document).where(Document.status == DocumentStatus.pending)
            ),
            "complaints": await self._count(
                select(func.count()).select_from(Complaint).where(Complaint.status == ComplaintStatus.open)
            ),
        }
