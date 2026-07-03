---
description: Запустить новый доменный модуль backend по правилам проекта (TDD, vertical slice, UUIDv7)
argument-hint: <название сущности, напр. vacancy>
---

Создай новый доменный модуль `$ARGUMENTS` по правилам проекта:

1. Сверься с PLAN.md (§3 доменная модель, §6 API) — какие поля, статусы и эндпоинты у сущности `$ARGUMENTS`.
2. Работай строго по skill tdd-workflow: СНАЧАЛА падающий тест в `apps/api/tests/$ARGUMENTS/` (testcontainers, реальные Postgres/Redis/MinIO — skill testcontainers), потом код.
3. Структура — skill backend-structure: `apps/api/app/$ARGUMENTS/` с `router.py`, `service.py`, `repo.py`, `schemas.py`, `models.py`.
4. Модель — skill uuid-v7-keys: PK `<entity>_uuid` UUIDv7, генерация в БД (server_default uuidv7()); деньги, если есть, — skill money-ledger (целые копейки, леджер).
5. Миграция — только `alembic revision --autogenerate` + `alembic upgrade head`, ревизии руками не писать.
6. Защищённые эндпоинты — skill rbac-permissions: зависимость проверки прав + негативные тесты на запрет.
7. Никаких fake/seed данных (skill real-data-only) — пустые состояния честные.
8. Подключи роутер в `main.py`, добейся полностью зелёного прогона, покажи короткий отчёт (сделано/осталось).
