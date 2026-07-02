import logging
from pathlib import Path
from typing import Protocol

import anyio.to_thread
import boto3
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError

from app.core.config import Settings

logger = logging.getLogger(__name__)


class Storage(Protocol):
    """Хранилище файлов. Контент отдаётся только через API с проверкой прав (skill s3-documents-kyc)."""

    async def put(self, key: str, data: bytes, content_type: str) -> None: ...
    async def get(self, key: str) -> bytes: ...


class LocalStorage:
    """Фолбэк-хранилище: обычная папка. Используется, когда S3/MinIO недоступен."""

    def __init__(self, base_path: str):
        self.base = Path(base_path).resolve()
        self.base.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        path = (self.base / key).resolve()
        if not path.is_relative_to(self.base):
            raise ValueError(f"ключ выходит за пределы хранилища: {key}")
        return path

    async def put(self, key: str, data: bytes, content_type: str) -> None:
        path = self._path(key)

        def _write() -> None:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)

        await anyio.to_thread.run_sync(_write)

    async def get(self, key: str) -> bytes:
        path = self._path(key)
        return await anyio.to_thread.run_sync(path.read_bytes)


class S3Storage:
    def __init__(self, endpoint_url: str, access_key: str, secret_key: str, bucket: str):
        self.bucket = bucket
        self.client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=BotoConfig(connect_timeout=2, read_timeout=10, retries={"max_attempts": 1}),
        )

    async def ensure_bucket(self) -> None:
        def _ensure() -> None:
            try:
                self.client.head_bucket(Bucket=self.bucket)
            except ClientError:
                self.client.create_bucket(Bucket=self.bucket)

        await anyio.to_thread.run_sync(_ensure)

    async def put(self, key: str, data: bytes, content_type: str) -> None:
        await anyio.to_thread.run_sync(
            lambda: self.client.put_object(Bucket=self.bucket, Key=key, Body=data, ContentType=content_type)
        )

    async def get(self, key: str) -> bytes:
        def _get() -> bytes:
            return self.client.get_object(Bucket=self.bucket, Key=key)["Body"].read()

        return await anyio.to_thread.run_sync(_get)


async def build_storage(settings: Settings) -> Storage:
    """Выбор backend: local — папка; s3 — строго S3; auto — S3, при недоступности фолбэк в папку."""
    if settings.storage_backend == "local":
        return LocalStorage(settings.local_storage_path)

    s3 = S3Storage(
        endpoint_url=settings.s3_endpoint_url,
        access_key=settings.s3_access_key,
        secret_key=settings.s3_secret_key,
        bucket=settings.s3_bucket,
    )
    try:
        await s3.ensure_bucket()
        return s3
    except Exception as exc:
        if settings.storage_backend == "s3":
            raise
        logger.warning(
            "S3 недоступен (%s) — файлы будут храниться в локальной папке %s",
            exc,
            settings.local_storage_path,
        )
        return LocalStorage(settings.local_storage_path)
