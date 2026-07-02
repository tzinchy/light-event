from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://light_event:light_event@localhost:5432/light_event"
    redis_url: str = "redis://localhost:6379/0"

    s3_endpoint_url: str = "http://localhost:9000"
    s3_access_key: str = "light-event"
    s3_secret_key: str = ""
    s3_bucket: str = "light-event"

    # хранилище: auto — S3, а при его недоступности фолбэк в локальную папку
    storage_backend: str = "auto"  # auto | s3 | local
    local_storage_path: str = "var/storage"
    document_max_size_mb: int = 15

    # каталог желаемых ролей (из референса)
    desired_role_catalog: list[str] = [
        "Официант", "Бариста", "Хостес", "Бармен", "Повар", "Ресепшн", "Гардероб", "Промоутер",
    ]

    app_secret_key: str = ""

    # тарифы — целые копейки (skill money-ledger)
    vacancy_publish_fee_kop: int = 99_000
    company_test_fee_kop: int = 150_000
    platform_commission_pct: int = 6

    # OTP / сессии
    otp_ttl_sec: int = 300
    otp_request_limit: int = 3          # запросов кода на телефон за окно
    otp_request_window_sec: int = 600
    otp_verify_max_attempts: int = 5
    access_token_ttl_sec: int = 900
    refresh_token_ttl_sec: int = 60 * 60 * 24 * 30


@lru_cache
def get_settings() -> Settings:
    return Settings()
