FROM python:3.12-alpine AS runtime

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /srv/api
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PYTHONUNBUFFERED=1

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini docker-entrypoint.sh ./
RUN chmod +x docker-entrypoint.sh

EXPOSE 8000
CMD ["./docker-entrypoint.sh"]
