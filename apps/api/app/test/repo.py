from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.company.models import Company
from app.test.models import AttemptStatus, Test, TestAttempt, TestKind, TestQuestion, TestStatus


class TestRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    def add(self, obj) -> None:
        self.session.add(obj)

    async def assignable_ids(self, company_uuid: UUID, uuids: list[UUID]) -> set[UUID]:
        """Какие из uuid можно поставить в требования вакансии: опубликованные тесты
        своей компании или платформенные (PLAN §11.6-D)."""
        if not uuids:
            return set()
        result = await self.session.execute(
            select(Test.test_uuid).where(
                Test.test_uuid.in_(uuids),
                Test.status == TestStatus.published,
                or_(Test.company_uuid == company_uuid, Test.kind == TestKind.platform),
            )
        )
        return set(result.scalars())

    async def passed_ids(self, user_uuid: UUID, uuids: list[UUID]) -> set[UUID]:
        """Из заданных тестов — те, что пользователь успешно прошёл."""
        if not uuids:
            return set()
        result = await self.session.execute(
            select(TestAttempt.test_uuid)
            .where(
                TestAttempt.user_uuid == user_uuid,
                TestAttempt.test_uuid.in_(uuids),
                TestAttempt.passed.is_(True),
            )
            .distinct()
        )
        return set(result.scalars())

    async def get(self, test_uuid: UUID) -> Test | None:
        return await self.session.get(Test, test_uuid)

    async def get_for_update(self, test_uuid: UUID) -> Test | None:
        result = await self.session.execute(
            select(Test).where(Test.test_uuid == test_uuid).with_for_update()
        )
        return result.scalar_one_or_none()

    async def list_published(self) -> list[tuple[Test, str | None, int]]:
        questions_count = (
            select(func.count())
            .select_from(TestQuestion)
            .where(TestQuestion.test_uuid == Test.test_uuid)
            .correlate(Test)
            .scalar_subquery()
        )
        result = await self.session.execute(
            select(Test, Company.name, questions_count.label("questions_count"))
            .join(Company, Company.company_uuid == Test.company_uuid, isouter=True)
            .where(Test.status == TestStatus.published)
            .order_by(Test.test_uuid)
        )
        return [tuple(row) for row in result.all()]

    async def list_by_company(self, company_uuid: UUID) -> list[tuple[Test, int, int]]:
        """Тесты компании со счётчиками вопросов и успешных прохождений (для /org/tests)."""
        questions_count = (
            select(func.count())
            .select_from(TestQuestion)
            .where(TestQuestion.test_uuid == Test.test_uuid)
            .correlate(Test)
            .scalar_subquery()
        )
        passed_count = (
            select(func.count(func.distinct(TestAttempt.user_uuid)))
            .select_from(TestAttempt)
            .where(TestAttempt.test_uuid == Test.test_uuid, TestAttempt.passed.is_(True))
            .correlate(Test)
            .scalar_subquery()
        )
        result = await self.session.execute(
            select(Test, questions_count.label("questions_count"), passed_count.label("passed_count"))
            .where(Test.company_uuid == company_uuid)
            .order_by(Test.test_uuid)
        )
        return [tuple(row) for row in result.all()]

    async def questions(self, test_uuid: UUID) -> list[TestQuestion]:
        result = await self.session.execute(
            select(TestQuestion).where(TestQuestion.test_uuid == test_uuid).order_by(TestQuestion.position)
        )
        return list(result.scalars())

    async def get_attempt(self, attempt_uuid: UUID) -> TestAttempt | None:
        return await self.session.get(TestAttempt, attempt_uuid)

    async def last_attempts_by_user(self, user_uuid: UUID) -> list[TestAttempt]:
        result = await self.session.execute(
            select(TestAttempt)
            .where(TestAttempt.user_uuid == user_uuid)
            .order_by(TestAttempt.test_attempt_uuid)
        )
        return list(result.scalars())

    async def active_or_cooldown_attempt(self, test_uuid: UUID, user_uuid: UUID) -> TestAttempt | None:
        """Незавершённая попытка или последняя с активным cooldown."""
        result = await self.session.execute(
            select(TestAttempt)
            .where(TestAttempt.test_uuid == test_uuid, TestAttempt.user_uuid == user_uuid)
            .order_by(TestAttempt.test_attempt_uuid.desc())
        )
        for attempt in result.scalars():
            if attempt.status == AttemptStatus.in_progress:
                return attempt
            if attempt.cooldown_until is not None:
                return attempt
            break
        return None

    async def passed_company_test_users(self, company_uuid: UUID) -> set[UUID]:
        """Кандидаты с бейджем «Тест компании пройден» — одним запросом для списка откликов."""
        result = await self.session.execute(
            select(TestAttempt.user_uuid)
            .join(Test, Test.test_uuid == TestAttempt.test_uuid)
            .where(
                Test.company_uuid == company_uuid,
                Test.kind == TestKind.company,
                TestAttempt.passed.is_(True),
            )
            .distinct()
        )
        return set(result.scalars())

    async def list_pending_moderation(self) -> list[tuple[Test, str | None]]:
        """Очередь модерации: pending-тесты с названием компании (admin/requests)."""
        result = await self.session.execute(
            select(Test, Company.name)
            .join(Company, Company.company_uuid == Test.company_uuid, isouter=True)
            .where(Test.status == TestStatus.pending_moderation)
            .order_by(Test.updated_at)
        )
        return [tuple(row) for row in result.all()]
