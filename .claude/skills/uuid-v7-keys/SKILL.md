---
name: uuid-v7-keys
description: Правила первичных и внешних ключей — UUIDv7 везде, генерация в БД (server_default uuidv7(), PostgreSQL 18). Триггеры — «модель», «таблица», «PK», «FK», «id», «ключ», «uuid».
---

# Ключи: UUID v7 везде

- PK каждой таблицы — UUID v7 (сортируемый по времени), колонка `<entity>_uuid` (напр. `user_uuid`, `vacancy_uuid`, `company_uuid`).
- Все FK — тоже uuid, именуются `<referenced_entity>_uuid`.
- Генерация — на стороне БД: `server_default=text("uuidv7()")` — нативная функция PostgreSQL 18 (решение заказчика 2026-07-03, ранее генерировали в приложении). Python-генераторов uuid7 в коде нет.
- Следствие: ID появляется только после `flush()` (SQLAlchemy получает его через RETURNING). Не читать `<entity>_uuid` у несохранённого объекта; репозитории делают `flush()` в create-методах.
- `compare_server_default=True` уже включён в `alembic/env.py` — autogenerate видит изменения дефолтов.
- В API наружу отдаём эти же uuid — они безопасны для публикации. Никаких инкрементных int-id, в т.ч. внутренних.

Шаблон колонки:

```python
from uuid import UUID
from sqlalchemy import ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column

class Vacancy(Base):
    __tablename__ = "vacancy"
    vacancy_uuid: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("uuidv7()"))
    company_uuid: Mapped[UUID] = mapped_column(ForeignKey("company.company_uuid"))
```
