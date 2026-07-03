from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_session
from app.review.models import ReviewTargetType
from app.review.schemas import ReviewCreateIn, ReviewListOut, ReviewOut
from app.review.service import ReviewService
from app.user.models import User

router = APIRouter(prefix="/api/v1", tags=["review"])


def get_review_service(session: AsyncSession = Depends(get_session)) -> ReviewService:
    return ReviewService(session=session)


@router.post("/reviews", response_model=ReviewOut, status_code=201)
async def create_review(
    payload: ReviewCreateIn,
    actor: User = Depends(get_current_user),
    service: ReviewService = Depends(get_review_service),
) -> ReviewOut:
    return ReviewOut.model_validate(await service.create(actor, payload))


@router.get("/users/{user_uuid}/reviews", response_model=ReviewListOut)
async def user_reviews(
    user_uuid: UUID, service: ReviewService = Depends(get_review_service)
) -> ReviewListOut:
    return await service.list_for_target(ReviewTargetType.user, user_uuid)


@router.get("/companies/{company_uuid}/reviews", response_model=ReviewListOut)
async def company_reviews(
    company_uuid: UUID, service: ReviewService = Depends(get_review_service)
) -> ReviewListOut:
    return await service.list_for_target(ReviewTargetType.company, company_uuid)
