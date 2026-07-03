from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.review.models import Review, ReviewTargetType


class ReviewRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    def add(self, review: Review) -> None:
        self.session.add(review)

    async def get_by_author_and_application(self, author_uuid: UUID, application_uuid: UUID) -> Review | None:
        result = await self.session.execute(
            select(Review).where(
                Review.author_uuid == author_uuid, Review.application_uuid == application_uuid
            )
        )
        return result.scalar_one_or_none()

    async def list_for_target(self, target_type: ReviewTargetType, target_uuid: UUID) -> list[Review]:
        result = await self.session.execute(
            select(Review)
            .where(Review.target_type == target_type, Review.target_uuid == target_uuid)
            .order_by(Review.review_uuid.desc())
        )
        return list(result.scalars())

    async def aggregate_for_target(
        self, target_type: ReviewTargetType, target_uuid: UUID
    ) -> tuple[float | None, int]:
        result = await self.session.execute(
            select(func.avg(Review.rating), func.count()).where(
                Review.target_type == target_type, Review.target_uuid == target_uuid
            )
        )
        avg, count = result.one()
        return (float(avg) if avg is not None else None, count)
