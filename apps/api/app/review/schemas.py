from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class ReviewCreateIn(BaseModel):
    application_uuid: UUID
    rating: int = Field(ge=1, le=5)
    text: str | None = Field(default=None, max_length=1000)
    kind: Literal["about_org", "about_event", "about_worker"]


class ReviewOut(BaseModel):
    model_config = {"from_attributes": True}

    review_uuid: UUID
    application_uuid: UUID
    vacancy_uuid: UUID
    author_uuid: UUID
    target_type: str
    target_uuid: UUID
    rating: int
    text: str | None
    kind: str
    created_at: datetime


class ReviewListOut(BaseModel):
    """Список отзывов с агрегатами — рейтинг цели считается на лету (PLAN §3.7)."""

    avg_rating: float | None
    count: int
    items: list[ReviewOut]
