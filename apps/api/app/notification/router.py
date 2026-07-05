from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_session
from app.notification.schemas import NotificationListOut
from app.notification.service import NotificationService
from app.user.models import User

router = APIRouter(prefix="/api/v1/notifications", tags=["notification"])


def get_notification_service(session: AsyncSession = Depends(get_session)) -> NotificationService:
    return NotificationService(session=session)


@router.get("", response_model=NotificationListOut)
async def list_notifications(
    actor: User = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
) -> NotificationListOut:
    return await service.list(actor)


@router.post("/read")
async def mark_read(
    actor: User = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
) -> dict:
    await service.mark_read(actor)
    return {"ok": True}
