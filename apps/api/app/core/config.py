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
    worker_completion_fee_kop: int = 0  # плата за сотрудника после смены; включается тарифом (§11.10-B)
    platform_commission_pct: int = 6

    # брошенная попытка теста: повтор доступен через (референс «Повтор через 15:00»)
    test_cooldown_sec: int = 900

    # OTP / сессии
    otp_ttl_sec: int = 300
    otp_request_limit: int = 3          # запросов кода на телефон за окно
    otp_request_window_sec: int = 600
    otp_verify_max_attempts: int = 5
    access_token_ttl_sec: int = 9000
    refresh_token_ttl_sec: int = 60 * 60 * 24 * 30

    # SMS.ru: ключ с sms.ru; пустой — коды в лог (ConsoleSmsProvider).
    # На свой подтверждённый номер sms.ru шлёт бесплатно — хватает для разработки.
    sms_ru_api_key: str = ""

    # SMTP для кодов подтверждения почты (Brevo в проде, Mailpit в dev);
    # пустой host — фолбэк в ConsoleEmailProvider
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "light-event <no-reply@light-event.local>"
    smtp_use_tls: bool = False


@lru_cache n 
def get_settings() -> Settings:
    return Settings()
