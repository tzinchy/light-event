---
name: uuid-v7-keys
description: Правила первичных и внешних ключей — UUIDv7 везде, генерация в приложении. Триггеры — «модель», «таблица», «PK», «FK», «id», «ключ», «uuid».
---

# Ключи: UUID v7 везде

- PK каждой таблицы — UUID v7 (сортируемый по времени), колонка `<entity>_uuid` (напр. `user_uuid`, `vacancy_uuid`, `company_uuid`).
- Все FK — тоже uuid, именуются `<referenced_entity>_uuid`.
- Генерация — на стороне приложения библиотекой `uuid_utils` (`uuid_utils.uuid7()`), НЕ в БД (`server_default` для PK не использовать) — генерация детерминируемо перехватывается в тестах.
- В API наружу отдаём эти же uuid — они безопасны для публикации. Никаких инкрементных int-id, в т.ч. внутренних.

Шаблон колонки:

```python
from uuid import UUID
import uuid_utils
from sqlalchemy.orm import Mapped, mapped_column

def uuid7() -> UUID:
    return UUID(bytes=uuid_utils.uuid7().bytes)

class Vacancy(Base):
    __tablename__ = "vacancy"
    vacancy_uuid: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    company_uuid: Mapped[UUID] = mapped_column(ForeignKey("company.company_uuid"))
```
