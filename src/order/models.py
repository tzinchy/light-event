from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm.properties import ForeignKey
from sqlalchemy.sql.functions import user

from src.database.core import Base


class Order(Base):
    __tablename__ = "orders"
    name
    created_by_user_uuid: Mapped[PG_UUID] = MappedColumn(
        PG_UUID, ForeignKey("users.user_uuid"), nullable=False
    )
