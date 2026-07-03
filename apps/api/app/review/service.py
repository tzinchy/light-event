from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.models import ApplicationStatus
from app.application.repo import ApplicationRepo
from app.core.errors import DomainError
from app.core.permissions import ensure_permission
from app.review.models import Review, ReviewKind, ReviewTargetType
from app.review.repo import ReviewRepo
from app.review.schemas import ReviewCreateIn, ReviewListOut, ReviewOut
from app.user.models import User
from app.vacancy.repo import VacancyRepo


class ReviewService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = ReviewRepo(session)
        self.applications = ApplicationRepo(session)
        self.vacancies = VacancyRepo(session)

    async def create(self, actor: User, data: ReviewCreateIn) -> Review:
        application = await self.applications.get(data.application_uuid)
        if application is None:
            raise DomainError(404, "Заявка не найдена")
        vacancy = await self.vacancies.get(application.vacancy_uuid)

        kind = ReviewKind(data.kind)
        if kind is ReviewKind.about_worker:
            # о работнике — команда компании с правом найма
            await ensure_permission(self.session, actor, vacancy.company_uuid, "hire")
            target_type, target_uuid = ReviewTargetType.user, application.user_uuid
        else:
            # об организации/событии — сам соискатель по своей заявке
            if application.user_uuid != actor.user_uuid:
                raise DomainError(403, "Отзыв можно оставить только по своей заявке")
            target_type, target_uuid = ReviewTargetType.company, vacancy.company_uuid

        if application.status not in (ApplicationStatus.paid, ApplicationStatus.done):
            raise DomainError(409, "Отзыв доступен после выплаты за смену")
        if await self.repo.get_by_author_and_application(actor.user_uuid, application.application_uuid):
            raise DomainError(409, "Отзыв по этой заявке уже оставлен")

        review = Review(
            application_uuid=application.application_uuid,
            vacancy_uuid=vacancy.vacancy_uuid,
            author_uuid=actor.user_uuid,
            target_type=target_type,
            target_uuid=target_uuid,
            rating=data.rating,
            text=data.text,
            kind=kind,
        )
        self.repo.add(review)
        await self.session.flush()
        return review

    async def list_for_target(self, target_type: ReviewTargetType, target_uuid: UUID) -> ReviewListOut:
        items = await self.repo.list_for_target(target_type, target_uuid)
        avg, count = await self.repo.aggregate_for_target(target_type, target_uuid)
        return ReviewListOut(
            avg_rating=avg, count=count, items=[ReviewOut.model_validate(r) for r in items]
        )
