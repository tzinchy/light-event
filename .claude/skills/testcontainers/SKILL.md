---
name: testcontainers
description: Интеграционные тесты на реальных Postgres/Redis/MinIO через testcontainers. Триггеры — «тест», «pytest», «фикстура», «conftest», «интеграционный».
---

# Testcontainers: реальные сервисы в тестах

- Интеграционные тесты поднимают реальные Postgres/Redis/MinIO в Docker через testcontainers. Никаких SQLite-подмен, fakeredis или мока S3.
- Контейнеры — session-scoped фикстуры (один старт на прогон); изоляция тестов — транзакция с rollback либо truncate между тестами.
- Схема БД в тестах — только `alembic upgrade head` против контейнера (никакого `create_all`). Это заодно проверяет сами миграции.
- Фикстурные данные создаются внутри теста через реальные repo/service/API (не сырыми INSERT в обход логики, кроме проверок самих repo).
- Внешние провайдеры (SMS, OAuth, платежи) — за интерфейсом; в тестах подставляется тестовая реализация интерфейса, у которой можно прочитать, что было отправлено (напр. OTP-код).
- e2e (Playwright) гоняются против compose-стенда `docker-compose.test.yml`.
