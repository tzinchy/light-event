# light-event

Платформа найма временного персонала для отелей, ресторанов и событий: соискатели ↔ организации ↔ администрация платформы. Монорепозиторий. План и доменная модель — в [PLAN.md](PLAN.md).

## Структура

```
apps/api               # FastAPI + SQLAlchemy 2 (async) + Alembic, Python 3.12 (uv)
apps/web               # Next.js (App Router) + shadcn/ui + Tailwind, mobile-first
packages/shared-types  # TS-клиент, генерируемый из OpenAPI
infra/                 # docker-compose (postgres, redis, minio, mailpit, api, web, nginx)
```

## Быстрый старт (dev)

```bash
cp .env.example .env            # заполнить пароли
make infra                      # postgres + redis + minio + mailpit в docker
cd apps/api && uv sync          # зависимости backend
make api                        # миграции + uvicorn на :8000
make web                        # next dev на :3000 (/api проксируется на :8000)
```

Письма (коды подтверждения почты) в dev уходят в Mailpit: http://localhost:8025.
SMS-коды печатаются в консоль API (`ConsoleSmsProvider`); прод — `SmsRuProvider` (env `SMS_RU_API_KEY`).

## Полный стенд (как в проде: всё в docker за nginx)

```bash
make full                       # сборка и запуск с профилем full
# http://localhost:8080         # nginx: / → web, /api → api, /ws → api
```

## Тесты

```bash
make test-api                   # pytest + testcontainers (нужен запущенный Docker)
make test-web                   # Vitest + Testing Library
make e2e                        # Playwright против полного стенда (:8080, см. make full)
```

Интеграционные тесты API сами поднимают реальные Postgres/Redis/MinIO в контейнерах и применяют миграции Alembic — локальная инфраструктура не нужна. E2E перехватывают коды через реальные интерфейсы: SMS — из Redis, письмо — из Mailpit HTTP API. Dev-стенд вместо полного: `make e2e E2E_BASE_URL=http://localhost:3000`.

## Миграции

```bash
make revision m="описание"     # alembic revision --autogenerate
make migrate                    # alembic upgrade head
```

## OpenAPI → TypeScript

```bash
make openapi-client             # openapi.json + regen packages/shared-types
```

## Администратор платформы

Первый админ назначается оператором сервера (не сид-данные):

```bash
cd apps/api && uv run python -m app.cli grant-admin +79990000000
```

Дальше — кабинет `/admin`: модерация заявок организаций, публикаций, пополнений, KYC.
