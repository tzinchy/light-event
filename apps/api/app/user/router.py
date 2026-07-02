from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_session
from app.user.models import User
from app.user.schemas import UserOut, UserUpdateIn
from app.user.service import UserService

router = APIRouter(prefix="/api/v1/users", tags=["users"])


def get_user_service(request: Request, session: AsyncSession = Depends(get_session)) -> UserService:
    return UserService(session=session, settings=request.app.state.settings)


@router.get("/me", response_model=UserOut)
async def get_me(user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(user)


@router.patch("/me", response_model=UserOut)
async def update_me(
    payload: UserUpdateIn,
    user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> UserOut:
    return UserOut.model_validate(await service.update_profile(user, payload))
