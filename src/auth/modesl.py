from ctypes import ARRAY
from datetime import date, datetime, timezone
from enum import StrEnum
from uuid import UUID

from sqlalchemy import Computed, Date, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, MappedColumn

from src.auth.enums import SexEnum
from src.database.core import Base


class UserRoles(Base):
    __tablename__ = "user_roles"
    user_role_id: Mapped[int] = MappedColumn(Integer, primary_key=True)
    user_role: Mapped[str] = MappedColumn(String, nullable=False)


class UserStatus(Base):
    __tablename__ = "user_status"
    user_status_id: Mapped[int] = MappedColumn(Integer, primary_key=True)
    user_status: Mapped[str] = MappedColumn(String, nullable=False)


class MedCardTypes(Base):
    __tablename__ = "med_card_types"
    med_card_type_id: Mapped[int] = MappedColumn(Integer, primary_key=True)
    med_card_type: Mapped[str] = MappedColumn(String, nullable=False)


class MedCards(Base):
    __tablename__ = "med_cards"
    med_card_id: Mapped[int] = MappedColumn(Integer, primary_key=True)
    medcard_name: Mapped[str] = MappedColumn(String, nullable=False)
    med_card_type_id: Mapped[int] = MappedColumn(
        Integer, ForeignKey("med_card_types.med_card_type_id"), nullable=False
    )


class Users(Base):
    __tablename__ = "users"
    user_uuid: Mapped[UUID] = MappedColumn(PG_UUID, primary_key=True)
    username: Mapped[str] = MappedColumn(String, nullable=True, unique=True)
    password: Mapped[str] = MappedColumn(String, nullable=False)
    first_name: Mapped[str] = MappedColumn(String, nullable=False)
    middle_name: Mapped[str | None] = MappedColumn(String, nullable=True)
    last_name: Mapped[str] = MappedColumn(String, nullable=False)
    email: Mapped[str | None] = MappedColumn(String, nullable=True)
    phone_number: Mapped[str] = MappedColumn(String, nullable=False)
    city: Mapped[str] = MappedColumn(String, nullable=False)
    sex: Mapped[SexEnum] = MappedColumn(String, nullable=False)
    birth_date: Mapped[date] = MappedColumn(String, nullable=False)
    languages: Mapped[dict | None] = MappedColumn(JSONB, nullable=True)
    user_status: Mapped[int] = MappedColumn(
        Integer, ForeignKey("user_status.user_status_id"), nullable=False
    )
    user_account_status: Mapped[int] = MappedColumn(
        Integer,
        ForeignKey("user_account_status.user_account_status_id"),
        nullable=False,
    )
    user_roles: Mapped[list[int]] = MappedColumn(
        ARRAY,
        nullable=False,
    )
    telegram_tag: Mapped[str | None] = MappedColumn(String, nullable=True)
    telegram_link: Mapped[str | None] = MappedColumn(
        Computed(f"https://t.me/{telegram_tag}"), nullable=True
    )


class UserMedCards(Base):
    __tablename__ = "user_med_cards"
    user_med_card_id: Mapped[int] = MappedColumn(Integer, primary_key=True)
    user_uuid: Mapped[UUID] = MappedColumn(
        PG_UUID, ForeignKey("users.user_uuid"), nullable=False
    )
    med_card_id: Mapped[int] = MappedColumn(
        Integer, ForeignKey("med_cards.med_card_id"), nullable=False
    )
    med_card_created: Mapped[date] = MappedColumn(
        Date, nullable=False, default=datetime.now(timezone.utc)
    )
