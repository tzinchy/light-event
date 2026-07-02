from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.errors import DomainError
from app.user.models import User
from app.user.repo import UserRepo
from app.user.schemas import UserUpdateIn


class UserService:
    def __init__(self, session: AsyncSession, settings: Settings):
        self.session = session
        self.settings = settings
        self.users = UserRepo(session)

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
        await self.session.flush()
        return user
