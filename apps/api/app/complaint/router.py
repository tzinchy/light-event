from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.complaint.schemas import ComplaintCreateIn, ComplaintOut, ComplaintResolveIn
from app.complaint.service import ComplaintService
from app.core.deps import get_current_user, get_session
from app.core.permissions import require_admin
from app.user.models import User

router = APIRouter(prefix="/api/v1", tags=["complaint"])


def get_complaint_service(session: AsyncSession = Depends(get_session)) -> ComplaintService:
    return ComplaintService(session=session)


@router.post("/complaints", response_model=ComplaintOut, status_code=201)
async def create_complaint(
    payload: ComplaintCreateIn,
    actor: User = Depends(get_current_user),
    service: ComplaintService = Depends(get_complaint_service),
) -> ComplaintOut:
    return ComplaintOut.model_validate(await service.create(actor, payload))


@router.get("/complaints/my", response_model=list[ComplaintOut])
async def my_complaints(
    actor: User = Depends(get_current_user),
    service: ComplaintService = Depends(get_complaint_service),
) -> list[ComplaintOut]:
    return [ComplaintOut.model_validate(c) for c in await service.list_my(actor)]


@router.get(
    "/admin/complaints", response_model=list[ComplaintOut], dependencies=[Depends(require_admin())]
)
async def admin_open_complaints(
    service: ComplaintService = Depends(get_complaint_service),
) -> list[ComplaintOut]:
    return [ComplaintOut.model_validate(c) for c in await service.list_open()]


@router.post("/admin/complaints/{complaint_uuid}/resolve", response_model=ComplaintOut)
async def admin_resolve_complaint(
    complaint_uuid: UUID,
    payload: ComplaintResolveIn,
    admin: User = Depends(require_admin()),
    service: ComplaintService = Depends(get_complaint_service),
) -> ComplaintOut:
    return ComplaintOut.model_validate(await service.resolve(admin, complaint_uuid, payload))
