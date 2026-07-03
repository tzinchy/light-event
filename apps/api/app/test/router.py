from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_session
from app.core.permissions import require_admin
from app.test.schemas import (
    AnswerIn,
    AttemptOut,
    AttemptWithQuestionsOut,
    CompanyTestItemOut,
    ModerateIn,
    MyResultOut,
    QuestionOut,
    TestCreateIn,
    TestListItemOut,
    TestOut,
)
from app.test.service import TestService
from app.user.models import User

router = APIRouter(prefix="/api/v1", tags=["tests"])


def get_test_service(request: Request, session: AsyncSession = Depends(get_session)) -> TestService:
    return TestService(session=session, settings=request.app.state.settings)


@router.get("/tests", response_model=list[TestListItemOut])
async def list_tests(
    user: User = Depends(get_current_user),
    service: TestService = Depends(get_test_service),
) -> list[TestListItemOut]:
    rows = await service.list_for_user(user)
    return [
        TestListItemOut(
            **TestOut.model_validate(test).model_dump(),
            company_name=company_name,
            questions_count=questions_count,
            my_result=MyResultOut(passed=best.passed, score_pct=best.score_pct) if best else None,
            cooldown_until=cooldown,
        )
        for test, company_name, questions_count, best, cooldown in rows
    ]


@router.get("/companies/{company_uuid}/tests", response_model=list[CompanyTestItemOut])
async def company_tests(
    company_uuid: UUID,
    user: User = Depends(get_current_user),
    service: TestService = Depends(get_test_service),
) -> list[CompanyTestItemOut]:
    return [
        CompanyTestItemOut(
            **TestOut.model_validate(test).model_dump(),
            questions_count=questions_count,
            passed_count=passed_count,
        )
        for test, questions_count, passed_count in await service.list_for_company(user, company_uuid)
    ]


@router.post("/companies/{company_uuid}/tests", response_model=TestOut, status_code=201)
async def create_company_test(
    company_uuid: UUID,
    payload: TestCreateIn,
    user: User = Depends(get_current_user),
    service: TestService = Depends(get_test_service),
) -> TestOut:
    return TestOut.model_validate(await service.create_company_test(user, company_uuid, payload))


@router.post("/admin/tests", response_model=TestOut, status_code=201, dependencies=[Depends(require_admin())])
async def create_platform_test(
    payload: TestCreateIn,
    service: TestService = Depends(get_test_service),
) -> TestOut:
    return TestOut.model_validate(await service.create_platform_test(payload))


@router.post(
    "/admin/tests/{test_uuid}/moderate", response_model=TestOut, dependencies=[Depends(require_admin())]
)
async def moderate_test(
    test_uuid: UUID,
    payload: ModerateIn,
    service: TestService = Depends(get_test_service),
) -> TestOut:
    return TestOut.model_validate(await service.moderate(test_uuid, payload))


@router.post("/tests/{test_uuid}/attempts", response_model=AttemptWithQuestionsOut, status_code=201)
async def start_attempt(
    test_uuid: UUID,
    user: User = Depends(get_current_user),
    service: TestService = Depends(get_test_service),
) -> AttemptWithQuestionsOut:
    attempt, questions = await service.start_attempt(user, test_uuid)
    return AttemptWithQuestionsOut(
        **AttemptOut.model_validate(attempt).model_dump(),
        questions=[QuestionOut.model_validate(q) for q in questions],
    )


@router.post("/attempts/{attempt_uuid}/answers", response_model=AttemptOut)
async def answer(
    attempt_uuid: UUID,
    payload: AnswerIn,
    user: User = Depends(get_current_user),
    service: TestService = Depends(get_test_service),
) -> AttemptOut:
    return AttemptOut.model_validate(await service.answer(user, attempt_uuid, payload))


@router.post("/attempts/{attempt_uuid}/finish", response_model=AttemptOut)
async def finish_attempt(
    attempt_uuid: UUID,
    user: User = Depends(get_current_user),
    service: TestService = Depends(get_test_service),
) -> AttemptOut:
    return AttemptOut.model_validate(await service.finish(user, attempt_uuid))


@router.post("/attempts/{attempt_uuid}/abandon", response_model=AttemptOut)
async def abandon_attempt(
    attempt_uuid: UUID,
    user: User = Depends(get_current_user),
    service: TestService = Depends(get_test_service),
) -> AttemptOut:
    return AttemptOut.model_validate(await service.abandon(user, attempt_uuid))
