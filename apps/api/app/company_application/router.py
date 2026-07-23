from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Request, Response, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.company_application.models import ApplicationStatus
from app.company_application.schemas import (
    AdminApplicationOut,
    ApplicationApproveOut,
    ApplicationRejectIn,
    ApplicationSubmitIn,
    ApplicationSubmitOut,
)
from app.company_application.service import AdminApplicationService, PublicApplicationService
from app.core.deps import get_session
from app.core.permissions import require_admin

# --- публичный приём заявок (без авторизации) ---
router = APIRouter(prefix="/api/v1/company-applications", tags=["company-applications"])


def get_public_service(request: Request, session: AsyncSession = Depends(get_session)) -> PublicApplicationService:
    return PublicApplicationService(
        session=session,
        storage=request.app.state.storage,
        max_size_mb=request.app.state.settings.document_max_size_mb,
    )


@router.post("", response_model=ApplicationSubmitOut, status_code=201)
async def submit_application(
    payload: ApplicationSubmitIn,
    service: PublicApplicationService = Depends(get_public_service),
) -> ApplicationSubmitOut:
    application = await service.submit(payload)
    return ApplicationSubmitOut(
        company_application_uuid=application.company_application_uuid,
        status=application.status.value,
        upload_token=application.upload_token,
    )


@router.post("/{application_uuid}/document", status_code=200)
async def attach_document(
    application_uuid: UUID,
    token: str = Form(...),
    file: UploadFile = File(...),
    service: PublicApplicationService = Depends(get_public_service),
) -> dict:
    await service.attach_document(application_uuid, token, await file.read(), file.content_type or "")
    return {"ok": True}


# --- модерация заявок админом ---
admin_router = APIRouter(
    prefix="/api/v1/admin/company-applications",
    tags=["company-applications"],
    dependencies=[Depends(require_admin())],
)


def get_admin_service(request: Request, session: AsyncSession = Depends(get_session)) -> AdminApplicationService:
    return AdminApplicationService(session=session, storage=request.app.state.storage)


@admin_router.get("", response_model=list[AdminApplicationOut])
async def list_applications(
    status: ApplicationStatus = ApplicationStatus.pending,
    service: AdminApplicationService = Depends(get_admin_service),
) -> list[AdminApplicationOut]:
    return await service.list_by_status(status)


@admin_router.get("/{application_uuid}/document")
async def application_document(
    application_uuid: UUID,
    service: AdminApplicationService = Depends(get_admin_service),
) -> Response:
    data, mime = await service.proof_content(application_uuid)
    return Response(content=data, media_type=mime)


@admin_router.post("/{application_uuid}/approve", response_model=ApplicationApproveOut)
async def approve_application(
    application_uuid: UUID,
    service: AdminApplicationService = Depends(get_admin_service),
) -> ApplicationApproveOut:
    application = await service.approve(application_uuid)
    return ApplicationApproveOut(
        company_application_uuid=application.company_application_uuid,
        status=application.status.value,
        company_uuid=application.company_uuid,
    )


@admin_router.post("/{application_uuid}/reject", response_model=AdminApplicationOut)
async def reject_application(
    application_uuid: UUID,
    payload: ApplicationRejectIn,
    service: AdminApplicationService = Depends(get_admin_service),
) -> AdminApplicationOut:
    application = await service.reject(application_uuid, payload.reason)
    return AdminApplicationOut.model_validate(application).model_copy(
        update={"has_document": application.proof_storage_key is not None}
    )
