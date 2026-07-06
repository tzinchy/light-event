from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.errors import DomainError
from app.pricing.repo import PricingRepo

# услуга → (человекочитаемое имя, атрибут дефолта в Settings)
PRICING_CATALOG: dict[str, tuple[str, str]] = {
    "vacancy_publish": ("Публикация события", "vacancy_publish_fee_kop"),
    "company_test": ("Тест компании", "company_test_fee_kop"),
    "worker_completion": ("Плата за сотрудника (после смены)", "worker_completion_fee_kop"),
}


class PricingService:
    def __init__(self, session: AsyncSession, settings: Settings):
        self.settings = settings
        self.repo = PricingRepo(session)

    def _default(self, key: str) -> int:
        return getattr(self.settings, PRICING_CATALOG[key][1])

    async def fee(self, key: str, company_uuid: UUID | None = None) -> int:
        """Актуальная цена: тариф компании → глобальный override → дефолт из конфига (§11.10-A)."""
        if company_uuid is not None:
            row = await self.repo.get(key, company_uuid)
            if row is not None:
                return row.amount_kop
        row = await self.repo.get(key)
        return row.amount_kop if row is not None else self._default(key)

    async def list_prices(self, company_uuid: UUID | None = None) -> list[dict]:
        """Эффективные цены; для компании помечаем, какие переопределены именно для неё."""
        global_overrides = await self.repo.all()
        company_overrides = await self.repo.all(company_uuid) if company_uuid is not None else {}
        out = []
        for key, (label, _attr) in PRICING_CATALOG.items():
            effective = company_overrides.get(key, global_overrides.get(key, self._default(key)))
            out.append(
                {
                    "key": key,
                    "label": label,
                    "amount_kop": effective,
                    "company_override": key in company_overrides,
                }
            )
        return out

    async def set_price(self, key: str, amount_kop: int, company_uuid: UUID | None = None) -> dict:
        if key not in PRICING_CATALOG:
            raise DomainError(404, "Неизвестная услуга")
        if amount_kop < 0:
            raise DomainError(422, "Цена не может быть отрицательной")
        await self.repo.upsert(key, amount_kop, company_uuid)
        return {
            "key": key,
            "label": PRICING_CATALOG[key][0],
            "amount_kop": amount_kop,
            "company_override": company_uuid is not None,
        }
