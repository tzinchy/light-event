from pydantic import BaseModel, Field


class PriceOut(BaseModel):
    key: str
    label: str
    amount_kop: int
    company_override: bool = False


class PriceUpdateIn(BaseModel):
    amount_kop: int = Field(ge=0)
