from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class QuestionIn(BaseModel):
    text: str = Field(min_length=5, max_length=500)
    multi: bool = False
    options: list[str] = Field(min_length=2, max_length=8)
    correct_indices: list[int] = Field(min_length=1)

    @model_validator(mode="after")
    def indices_valid(self):
        if any(i < 0 or i >= len(self.options) for i in self.correct_indices):
            raise ValueError("Индекс верного варианта вне диапазона options")
        if not self.multi and len(self.correct_indices) != 1:
            raise ValueError("У одиночного вопроса ровно один верный вариант")
        return self


class TestCreateIn(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    topic: str = Field(min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=1000)
    min_correct: int = Field(ge=1)
    questions: list[QuestionIn] = Field(min_length=1, max_length=50)

    @model_validator(mode="after")
    def min_correct_reachable(self):
        if self.min_correct > len(self.questions):
            raise ValueError("Порог выше числа вопросов")
        return self


class TestOut(BaseModel):
    model_config = {"from_attributes": True}

    test_uuid: UUID
    kind: str
    company_uuid: UUID | None
    title: str
    topic: str
    description: str | None
    min_correct: int
    status: str
    reject_reason: str | None
    created_at: datetime


class MyResultOut(BaseModel):
    passed: bool
    score_pct: int


class TestListItemOut(TestOut):
    """Строка каталога тестов: прогресс пользователя поверх теста."""

    company_name: str | None = None
    questions_count: int
    my_result: MyResultOut | None = None
    cooldown_until: datetime | None = None


class CompanyTestItemOut(TestOut):
    """Строка списка тестов в кабинете организации."""

    questions_count: int
    passed_count: int


class QuestionOut(BaseModel):
    """Вопрос для прохождения — без correct_indices (skill real-data-only §ответы)."""

    model_config = {"from_attributes": True}

    test_question_uuid: UUID
    position: int
    text: str
    multi: bool
    options: list[str]


class AttemptOut(BaseModel):
    model_config = {"from_attributes": True}

    test_attempt_uuid: UUID
    test_uuid: UUID
    status: str
    correct_count: int
    score_pct: int
    passed: bool
    cooldown_until: datetime | None


class AttemptWithQuestionsOut(AttemptOut):
    questions: list[QuestionOut]


class AnswerIn(BaseModel):
    test_question_uuid: UUID
    selected_indices: list[int] = Field(min_length=1)


class ModerateIn(BaseModel):
    action: Literal["approve", "reject"]
    reason: str | None = Field(default=None, max_length=500)
