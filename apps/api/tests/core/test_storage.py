from testcontainers.minio import MinioContainer

from app.core.config import Settings
from app.core.storage import LocalStorage, S3Storage, build_storage


async def test_s3_storage_roundtrip():
    with MinioContainer() as minio:
        cfg = minio.get_config()
        s3 = S3Storage(
            endpoint_url=f"http://{cfg['endpoint']}",
            access_key=cfg["access_key"],
            secret_key=cfg["secret_key"],
            bucket="test-bucket",
        )
        await s3.ensure_bucket()
        await s3.put("documents/a/b", b"hello-s3", "text/plain")
        assert await s3.get("documents/a/b") == b"hello-s3"


async def test_auto_fallback_creates_local_folder_when_s3_unreachable(tmp_path):
    settings = Settings(
        storage_backend="auto",
        s3_endpoint_url="http://127.0.0.1:1",  # заведомо недоступен
        local_storage_path=str(tmp_path / "store"),
        _env_file=None,
    )

    storage = await build_storage(settings)

    assert isinstance(storage, LocalStorage)
    assert (tmp_path / "store").is_dir()
    await storage.put("docs/x", b"local-bytes", "application/octet-stream")
    assert await storage.get("docs/x") == b"local-bytes"


async def test_local_storage_rejects_path_traversal(tmp_path):
    storage = LocalStorage(str(tmp_path / "store"))
    try:
        await storage.put("../outside", b"x", "text/plain")
    except ValueError:
        pass
    else:
        raise AssertionError("ожидали ValueError на выход за пределы папки")
