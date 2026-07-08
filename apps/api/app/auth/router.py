from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import MeOut, OtpRequestIn, OtpVerifyIn, RefreshIn, TokensOut
from app.auth.service import AuthService
from app.core.deps import get_current_user, get_session
from app.mailing.service import MailingService
from app.user.models import User

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def get_auth_service(request: Request, session: AsyncSession = Depends(get_session)) -> AuthService:
    state = request.app.state
    return AuthService(
        session=session,
        redis=state.redis,
        mailing=MailingService(state.session_factory, state.email_provider),
        settings=state.settings,
    )


@router.post("/otp/request", status_code=202)
async def request_otp(payload: OtpRequestIn, service: AuthService = Depends(get_auth_service)) -> dict:
    await service.request_otp(payload.email)
    return {"detail": "Код отправлен"}


@router.post("/otp/verify", response_model=TokensOut)
async def verify_otp(payload: OtpVerifyIn, service: AuthService = Depends(get_auth_service)) -> TokensOut:
    tokens, _ = await service.verify_otp(payload.email, payload.code)
    return TokensOut(**tokens)


@router.post("/refresh", response_model=TokensOut)
async def refresh(payload: RefreshIn, service: AuthService = Depends(get_auth_service)) -> TokensOut:
    tokens = await service.refresh(payload.refresh_token)
    return TokensOut(**tokens)


@router.post("/logout", status_code=204)
async def logout(
    payload: RefreshIn,
    service: AuthService = Depends(get_auth_service),
    user: User = Depends(get_current_user),
) -> None:
    await service.logout(payload.refresh_token)


@router.get("/me", response_model=MeOut)
async def me(user: User = Depends(get_current_user)) -> User:
    return user


@router.post("/consent", response_model=MeOut)
async def consent(
    user: User = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
) -> User:
    return await service.set_pd_consent(user)
