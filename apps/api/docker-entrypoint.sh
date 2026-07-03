#!/bin/sh
set -e

uv run --no-dev alembic upgrade head
exec uv run --no-dev uvicorn app.main:app --host 0.0.0.0 --port 8000
