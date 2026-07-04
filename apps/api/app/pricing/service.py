from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.errors import DomainError
from app.pricing.repo import PricingRepo

# услуга → (человекочитаемое имя, атрибут дефолта в Settings)
PRICING_CATALOG: dict[str, tuple[str, str]] = {
    "vacancy_publish": ("Публикация события", "vacancy_publish_fee_kop"),
    "company_test": ("Тест компании", "company_test_fee_kop"),
}


class PricingService:
    def __init__(self, session: AsyncSession, settings: Settings):
        self.settings = settings
        self.repo = PricingRepo(session)

    def _default(self, key: str) -> int:
        return getattr(self.settings, PRICING_CATALOG[key][1])

    async def fee(self, key: str) -> int:
        """Актуальная цена услуги: переопределение админа или дефолт из конфига."""
        row = await self.repo.get(key)
        return row.amount_kop if row is not None else self._default(key)

    async def list_prices(self) -> list[dict]:
        overrides = await self.repo.all()
        return [
            {"key": key, "label": label, "amount_kop": overrides.get(key, self._default(key))}
            for key, (label, _attr) in PRICING_CATALOG.items()
        ]

    async def set_price(self, key: str, amount_kop: int) -> dict:
        if key not in PRICING_CATALOG:
            raise DomainError(404, "Неизвестная услуга")
        if amount_kop < 0:
            raise DomainError(422, "Цена не может быть отрицательной")
        await self.repo.upsert(key, amount_kop)
        return {"key": key, "label": PRICING_CATALOG[key][0], "amount_kop": amount_kop}
