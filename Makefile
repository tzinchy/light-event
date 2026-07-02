.PHONY: infra infra-down api web test-api test-web migrate revision openapi-client

# postgres + redis + minio для локальной разработки
infra:
	docker compose -f infra/docker-compose.yml up -d db redis minio minio-init

infra-down:
	docker compose -f infra/docker-compose.yml down

api:
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
