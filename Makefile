.PHONY: infra infra-down full full-rebuild prod api web test-api test-web migrate revision openapi-client e2e

# postgres + redis + minio для локальной разработки
infra:
	docker compose --env-file .env -f infra/docker-compose.yml up -d db redis minio minio-init

infra-down:
	docker compose --env-file .env -f infra/docker-compose.yml down

# полный стенд: db + redis + minio + api + web + nginx (http://localhost:8080)
full:
	docker compose --env-file .env -f infra/docker-compose.yml --profile full up -d --build

# прод: полный стенд + Caddy с HTTPS (адрес — SITE_ADDRESS из .env, порты 80/443)
prod:
	docker compose --env-file .env -f infra/docker-compose.yml --profile full --profile prod up -d --build

# форс: образы без кэша + пересоздание контейнеров (данные в томах не трогает)
full-rebuild:
	docker compose --env-file .env -f infra/docker-compose.yml --profile full build --no-cache
	docker compose --env-file .env -f infra/docker-compose.yml --profile full up -d --force-recreate

api: migrate
	cd apps/api && uv run uvicorn app.main:app --reload --port 8000

web:
	pnpm --filter web dev

test-api:
	cd apps/api && uv run pytest

test-web:
	pnpm --filter web test

migrate:
	cd apps/api && uv run alembic upgrade head

# make revision m="описание"
revision:
	cd apps/api && uv run alembic revision --autogenerate -m "$(m)"

openapi-client:
	cd apps/api && uv run python -c "import json; from app.main import app; print(json.dumps(app.openapi(), ensure_ascii=False))" > ../../packages/shared-types/openapi.json
	pnpm --filter @light-event/shared-types generate

# e2e против полного стенда (make full); можно перекрыть: make e2e E2E_BASE_URL=http://localhost:3000
E2E_BASE_URL ?= http://localhost:8080
e2e:
	E2E_BASE_URL=$(E2E_BASE_URL) pnpm --filter web exec playwright test
