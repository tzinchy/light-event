# light-event

Платформа найма временного персонала для отелей, ресторанов и событий: соискатели ↔ организации ↔ администрация платформы. Монорепозиторий. План и доменная модель — в [PLAN.md](PLAN.md).

## Структура

```
apps/api          # FastAPI + SQLAlchemy 2 (async) + Alembic
apps/web          # Next.js (App Router) + shadcn/ui + Tailwind  (этап 14)
packages/shared-types  # TS-клиент, генерируемый из OpenAPI
infra/            # docker-compose (postgres, redis, minio, api, nginx), nginx
```

## Быстрый старт (dev)

```bash
cp .env.example .env            # заполнить пароли
make infra                      # postgres + redis + minio в docker
cd apps/api && uv sync          # зависимости backend
make migrate                    # alembic upgrade head
make api                        # uvicorn на :8000
```

## Тесты

```bash
make test-api                   # pytest + testcontainers (нужен запущенный Docker)
```

Интеграционные тесты сами поднимают реальные Postgres/Redis/MinIO в контейнерах и применяют миграции Alembic — локальная инфраструктура не нужна.

## Миграции

```bash
make revision m="описание"     # alembic revision --autogenerate
make migrate                    # alembic upgrade head
```

## Полный стенд (api за nginx)

```bash
docker compose -f infra/docker-compose.yml --profile full up --build
# nginx: http://localhost:8080  (/api → FastAPI; / → web на этапе фронтенда)
```
