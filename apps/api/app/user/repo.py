from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.document.models import Document
from app.user.models import ModerationStatus, User


class UserRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, user_uuid: UUID) -> User | None:
        return await self.session.get(User, user_uuid)

    async def list_for_admin(
        self,
        *,
        status: ModerationStatus | None = None,
        query: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[tuple[User, int]]:
        """Пользователи для админки: (user, число документов), новые сверху."""
        doc_count = func.count(Document.document_uuid)
        stmt = (
            select(User, doc_count)
            .outerjoin(Document, Document.owner_uuid == User.user_uuid)
            .group_by(User.user_uuid)
            .order_by(User.user_uuid.desc())
            .limit(limit)
            .offset(offset)
        )
        if status is not None:
            stmt = stmt.where(User.moderation_status == status)
        if query:
            like = f"%{query}%"
            stmt = stmt.where(or_(User.email.ilike(like), User.name.ilike(like)))
        result = await self.session.execute(stmt)
        return [(row[0], row[1]) for row in result.all()]

    async def get_by_phone(self, phone: str) -> User | None:
        result = await self.session.execute(select(User).where(User.phone == phone))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def create_with_email(self, email: str) -> User:
        """Регистрация по e-mail-OTP: почта сразу подтверждена самим фактом входа."""
        user = User(email=email, email_verified_at=datetime.now(timezone.utc))
        self.session.add(user)
        await self.session.flush()
        return user

    async def set_pd_consent(self, user: User) -> User:
        user.pd_consent_at = datetime.now(timezone.utc)
        await self.session.flush()
        return user
