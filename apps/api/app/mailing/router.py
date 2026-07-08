from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_session
from app.core.permissions import require_admin
from app.mailing.repo import MailingRepo
from app.mailing.schemas import EmailMessageOut, EmailSendIn
from app.mailing.service import MailingService
from app.user.models import User

router = APIRouter(prefix="/api/v1/admin/emails", tags=["admin"])


def get_mailing_service(request: Request) -> MailingService:
    return MailingService(request.app.state.session_factory, request.app.state.email_provider)


@router.get("", response_model=list[EmailMessageOut], dependencies=[Depends(require_admin())])
async def list_emails(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> list[EmailMessageOut]:
    letters = await MailingRepo(session).list(limit=limit, offset=offset)
    return [EmailMessageOut.model_validate(m) for m in letters]


@router.post("/send", response_model=EmailMessageOut, status_code=201)
async def send_email(
    payload: EmailSendIn,
    admin: User = Depends(require_admin()),
    service: MailingService = Depends(get_mailing_service),
) -> EmailMessageOut:
    message = await service.send_custom(
        to_email=payload.to_email, subject=payload.subject, body=payload.body, created_by=admin.user_uuid
    )
    return EmailMessageOut.model_validate(message)
