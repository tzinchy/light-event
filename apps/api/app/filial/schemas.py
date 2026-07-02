from uuid import UUID

from pydantic import BaseModel, Field


class FilialCreateIn(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    address: str = Field(min_length=2, max_length=300)
    lat: float | None = Field(default=None, ge=-90, le=90)
    lon: float | None = Field(default=None, ge=-180, le=180)


class FilialUpdateIn(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    address: str | None = Field(default=None, min_length=2, max_length=300)
    lat: float | None = Field(default=None, ge=-90, le=90)
    lon: float | None = Field(default=None, ge=-180, le=180)


class FilialOut(BaseModel):
    model_config = {"from_attributes": True}

    filial_uuid: UUID
    company_uuid: UUID
    name: str
    address: str
    lat: float | None
    lon: float | None
