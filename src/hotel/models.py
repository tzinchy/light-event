from datetime import datetime

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, MappedColumn
from sqlalchemy.orm.properties import ForeignKey
from sqlalchemy.sql.sqltypes import DateTime

from src.database.core import Base


class Companies(Base):
    __tablename__ = "companies"
    company_id: Mapped[int] = MappedColumn(Integer, primary_key=True)
    company_name: Mapped[str] = MappedColumn(String, nullable=False)
    description: Mapped[str] = MappedColumn(String, nullable=True)
    law_address: Mapped[str] = MappedColumn(String, nullable=False)
    ogrn: Mapped[int] = MappedColumn(Integer, nullable=False)
    inn: Mapped[int] = MappedColumn(Integer, nullable=False)
    kpp: Mapped[int] = MappedColumn(Integer, nullable=False)
    authorized_capital: Mapped[datetime] = MappedColumn(Integer, nullable=False)
    registred_at: Mapped[DateTime] = MappedColumn(DateTime, nullable=False)


class CompanyFilials(Base):
    __tablename__ = "company_filials"
    filial_id: Mapped[int] = MappedColumn(Integer, primary_key=True)
    company_id: Mapped[int] = MappedColumn(
        Integer, ForeignKey("companies.company_id"), nullable=False
    )
    description: Mapped[str] = MappedColumn(String, nullable=True)
    address: Mapped[str] = MappedColumn(String, nullable=False)
    yandex_url: Mapped[str] = MappedColumn(String, nullable=True)
