from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import DomainError
from app.core.permissions import ensure_main_manager, ensure_membership
from app.filial.models import Filial
from app.filial.repo import FilialRepo
from app.filial.schemas import FilialCreateIn, FilialUpdateIn
from app.user.models import User


class FilialService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.filials = FilialRepo(session)

    async def create(self, user: User, company_uuid: UUID, data: FilialCreateIn) -> Filial:
        await ensure_main_manager(self.session, user, company_uuid)
        return await self.filials.create(company_uuid, data.name, data.address, data.lat, data.lon)

    async def list_for_member(self, user: User, company_uuid: UUID) -> list[Filial]:
        await ensure_membership(self.session, user, company_uuid)
        return await self.filials.list_by_company(company_uuid)

    async def _get_for_main_manager(self, user: User, filial_uuid: UUID) -> Filial:
        filial = await self.filials.get(filial_uuid)
        if filial is None:
            raise DomainError(404, "Филиал не найден")
        await ensure_main_manager(self.session, user, filial.company_uuid)
        return filial

    async def update(self, user: User, filial_uuid: UUID, data: FilialUpdateIn) -> Filial:
        filial = await self._get_for_main_manager(user, filial_uuid)
        for field in ("name", "address", "lat", "lon"):
            value = getattr(data, field)
            if value is not None:
                setattr(filial, field, value)
        await self.session.flush()
        return filial

    async def delete(self, user: User, filial_uuid: UUID) -> None:
        filial = await self._get_for_main_manager(user, filial_uuid)
        await self.filials.delete(filial)
