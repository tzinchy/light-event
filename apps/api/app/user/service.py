from datetime import datetime, timezone

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.errors import DomainError
from app.core.otp import OtpStore
from app.mailing.service import MailingService
from app.user.models import User
from app.user.repo import UserRepo
from app.user.schemas import UserUpdateIn


class UserService:
    def __init__(
        self,
        session: AsyncSession,
        settings: Settings,
        redis: Redis | None = None,
        mailing: MailingService | None = None,
    ):
        self.session = session
        self.settings = settings
        self.users = UserRepo(session)
        self.otp = OtpStore(redis, settings) if redis is not None else None
        self.mailing = mailing

    async def request_email_code(self, user: User, email: str) -> None:
        if user.email != email:
            user.email = email
            user.email_verified_at = None
            await self.session.flush()
        code = await self.otp.issue("email", email)
        await self.mailing.send_otp(email, code)

    async def confirm_email(self, user: User, code: str) -> User:
        if user.email is None:
            raise DomainError(401, "Код не запрошен или истёк")
        await self.otp.verify("email", user.email, code)
        user.email_verified_at = datetime.now(timezone.utc)
        await self.session.flush()
        return user

    async def update_profile(self, user: User, data: UserUpdateIn) -> User:
        if data.desired_roles is not None:
            unknown = set(data.desired_roles) - set(self.settings.desired_role_catalog)
            if unknown:
                raise DomainError(422, f"Неизвестные роли: {', '.join(sorted(unknown))}")
            user.desired_roles = data.desired_roles
        if data.name is not None:
            user.name = data.name
        if data.city is not None:
            user.city = data.city
        if data.experience is not None:
            user.experience = data.experience
        if data.about is not None:
            user.about = data.about
        if data.english_level is not None:
            user.english_level = data.english_level
        if data.education is not None:
            user.education = data.education
        if data.telegram is not None:
            user.telegram = data.telegram or None  # пустая строка = отвязать
        if data.birth_date is not None:
            user.birth_date = data.birth_date
        if data.citizenship is not None:
            user.citizenship = data.citizenship
        if data.gender is not None:
            user.gender = data.gender
        await self.session.flush()
        return user
