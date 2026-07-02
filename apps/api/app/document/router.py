from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Request, Response, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_session
from app.document.models import DocumentKind
from app.document.schemas import DocumentOut
from app.document.service import DocumentService
from app.user.models import User

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])


def get_document_service(request: Request, session: AsyncSession = Depends(get_session)) -> DocumentService:
    return DocumentService(session=session, storage=request.app.state.storage, settings=request.app.state.settings)


@router.post("", response_model=DocumentOut, status_code=201)
async def upload_document(
    kind: DocumentKind = Form(),
    file: UploadFile = File(),
    user: User = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
) -> DocumentOut:
    content = await file.read()
    doc = await service.upload(user, kind, content, file.content_type or "")
    return DocumentOut.model_validate(doc)


@router.get("/my", response_model=list[DocumentOut])
async def my_documents(
    user: User = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
) -> list[DocumentOut]:
    return [DocumentOut.model_validate(d) for d in await service.list_my(user)]


@router.get("/{document_uuid}/content")
async def document_content(
    document_uuid: UUID,
    user: User = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
) -> Response:
    data, mime = await service.get_content(user, document_uuid)
    return Response(content=data, media_type=mime)
