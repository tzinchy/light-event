from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.balance.models import PLATFORM_OWNER_UUID, AccountOwnerType, LedgerKind
from app.balance.repo import BalanceRepo
from app.balance.service import BalanceService
from app.core.config import Settings
from app.core.errors import DomainError
from app.core.permissions import ensure_membership, ensure_permission
from app.pricing.service import PricingService
from app.test.models import AttemptStatus, Test, TestAttempt, TestKind, TestQuestion, TestStatus
from app.test.repo import TestRepo
from app.test.schemas import AnswerIn, ModerateIn, TestCreateIn
from app.user.models import User


class TestService:
    def __init__(self, session: AsyncSession, settings: Settings):
        self.session = session
        self.settings = settings
        self.repo = TestRepo(session)
        self.balance = BalanceService(session)

    def _add_questions(self, test_uuid: UUID, data: TestCreateIn) -> None:
        for position, q in enumerate(data.questions):
            self.repo.add(
                TestQuestion(
                    test_uuid=test_uuid,
                    position=position,
                    text=q.text,
                    multi=q.multi,
                    options=q.options,
                    correct_indices=q.correct_indices,
                )
            )

    async def create_company_test(self, actor: User, company_uuid: UUID, data: TestCreateIn) -> Test:
        # создание — бесплатный черновик (баланс не нужен); плата берётся при отправке на модерацию
        await ensure_permission(self.session, actor, company_uuid, "create")
        test = Test(
            kind=TestKind.company,
            company_uuid=company_uuid,
            title=data.title,
            topic=data.topic,
            description=data.description,
            materials=data.materials,
            min_correct=data.min_correct,
            status=TestStatus.draft,
        )
        self.repo.add(test)
        await self.session.flush()
        self._add_questions(test.test_uuid, data)
        await self.session.flush()
        return test

    async def submit_for_moderation(self, actor: User, test_uuid: UUID) -> Test:
        # блокировка строки: параллельная отправка не спишет тариф дважды
        test = await self.repo.get_for_update(test_uuid)
        if test is None or test.kind != TestKind.company:
            raise DomainError(404, "Тест не найден")
        await ensure_permission(self.session, actor, test.company_uuid, "create")
        if test.status != TestStatus.draft:
            raise DomainError(409, "Отправить на модерацию можно только черновик")
        fee_kop = await PricingService(self.session, self.settings).fee("company_test", test.company_uuid)
        # оплата тарифа и отправка — одна транзакция (skill money-ledger)
        repo = BalanceRepo(self.session)
        company_account = await repo.get_or_create_account(AccountOwnerType.company, test.company_uuid)
        platform_account = await repo.get_or_create_account(AccountOwnerType.platform, PLATFORM_OWNER_UUID)
        await self.balance.transfer(
            debit_account_uuid=company_account.account_uuid,
            credit_account_uuid=platform_account.account_uuid,
            amount_kop=fee_kop,
            kind=LedgerKind.test_fee,
            ref_type="test",
            ref_uuid=test.test_uuid,
            comment=f"Отправка теста на модерацию · {test.title}",
        )
        test.price_kop = fee_kop
        test.status = TestStatus.pending_moderation
        await self.session.flush()
        return test

    async def create_platform_test(self, data: TestCreateIn) -> Test:
        """Платформенные тесты создаёт админ — публикуются сразу (PLAN §3.3)."""
        test = Test(
            kind=TestKind.platform,
            title=data.title,
            topic=data.topic,
            description=data.description,
            materials=data.materials,
            min_correct=data.min_correct,
            status=TestStatus.published,
        )
        self.repo.add(test)
        await self.session.flush()
        self._add_questions(test.test_uuid, data)
        await self.session.flush()
        return test

    async def moderate(self, test_uuid: UUID, data: ModerateIn) -> Test:
        test = await self.repo.get_for_update(test_uuid)
        if test is None:
            raise DomainError(404, "Тест не найден")
        if test.status != TestStatus.pending_moderation:
            raise DomainError(409, "Тест не находится на модерации")
        if data.action == "approve":
            test.status = TestStatus.published
        else:
            test.status = TestStatus.rejected
            test.reject_reason = data.reason
        await self.session.flush()
        return test

    async def list_for_user(self, actor: User):
        rows = await self.repo.list_published()
        attempts = await self.repo.last_attempts_by_user(actor.user_uuid)
        now = datetime.now(UTC)
        best: dict[UUID, TestAttempt] = {}
        cooldowns: dict[UUID, datetime] = {}
        for attempt in attempts:  # отсортированы по времени: последние перезаписывают
            if attempt.status == AttemptStatus.finished:
                current = best.get(attempt.test_uuid)
                if current is None or attempt.score_pct >= current.score_pct:
                    best[attempt.test_uuid] = attempt
            if attempt.cooldown_until is not None and attempt.cooldown_until > now:
                cooldowns[attempt.test_uuid] = attempt.cooldown_until
        return [
            (test, company_name, questions_count, best.get(test.test_uuid), cooldowns.get(test.test_uuid))
            for test, company_name, questions_count in rows
        ]

    async def list_for_company(self, actor: User, company_uuid: UUID):
        await ensure_membership(self.session, actor, company_uuid)
        return await self.repo.list_by_company(company_uuid)

    async def start_attempt(self, actor: User, test_uuid: UUID) -> tuple[TestAttempt, list[TestQuestion]]:
        test = await self.repo.get(test_uuid)
        if test is None:
            raise DomainError(404, "Тест не найден")
        if test.status != TestStatus.published:
            raise DomainError(409, "Тест не опубликован")
        existing = await self.repo.active_or_cooldown_attempt(test_uuid, actor.user_uuid)
        if existing is not None:
            if existing.status == AttemptStatus.in_progress:
                # возобновляем незавершённую попытку — отдаём её с сохранёнными ответами
                return existing, await self.repo.questions(test_uuid)
            if existing.cooldown_until and existing.cooldown_until > datetime.now(UTC):
                raise DomainError(409, "Повторная попытка будет доступна позже")
        attempt = TestAttempt(test_uuid=test_uuid, user_uuid=actor.user_uuid)
        self.repo.add(attempt)
        await self.session.flush()
        return attempt, await self.repo.questions(test_uuid)

    async def _own_attempt(self, actor: User, attempt_uuid: UUID, for_update: bool = False) -> TestAttempt:
        attempt = await self.repo.get_attempt(attempt_uuid)
        if attempt is None:
            raise DomainError(404, "Попытка не найдена")
        if attempt.user_uuid != actor.user_uuid:
            raise DomainError(403, "Это не ваша попытка")
        if attempt.status != AttemptStatus.in_progress:
            raise DomainError(409, "Попытка уже завершена")
        return attempt

    async def answer(self, actor: User, attempt_uuid: UUID, data: AnswerIn) -> TestAttempt:
        attempt = await self._own_attempt(actor, attempt_uuid)
        questions = {q.test_question_uuid: q for q in await self.repo.questions(attempt.test_uuid)}
        question = questions.get(data.test_question_uuid)
        if question is None:
            raise DomainError(404, "Вопрос не из этого теста")
        if any(i < 0 or i >= len(question.options) for i in data.selected_indices):
            raise DomainError(422, "Индекс варианта вне диапазона")
        # JSONB: присваиваем новый dict, чтобы SQLAlchemy увидел изменение
        attempt.answers = {**attempt.answers, str(data.test_question_uuid): sorted(data.selected_indices)}
        await self.session.flush()
        return attempt

    async def finish(self, actor: User, attempt_uuid: UUID) -> TestAttempt:
        attempt = await self._own_attempt(actor, attempt_uuid)
        test = await self.repo.get(attempt.test_uuid)
        questions = await self.repo.questions(attempt.test_uuid)
        correct = sum(
            1
            for q in questions
            if attempt.answers.get(str(q.test_question_uuid)) == sorted(q.correct_indices)
        )
        attempt.correct_count = correct
        attempt.score_pct = round(correct / len(questions) * 100) if questions else 0
        attempt.passed = correct >= test.min_correct
        attempt.status = AttemptStatus.finished
        attempt.finished_at = datetime.now(UTC)
        await self.session.flush()
        return attempt

    async def abandon(self, actor: User, attempt_uuid: UUID) -> TestAttempt:
        """Выход без завершения: прогресс 0, cooldown до повтора (референс «Повтор через…»)."""
        attempt = await self._own_attempt(actor, attempt_uuid)
        attempt.status = AttemptStatus.abandoned
        attempt.correct_count = 0
        attempt.score_pct = 0
        attempt.passed = False
        attempt.cooldown_until = datetime.now(UTC) + timedelta(seconds=self.settings.test_cooldown_sec)
        await self.session.flush()
        return attempt
