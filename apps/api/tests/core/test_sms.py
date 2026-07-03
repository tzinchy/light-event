import logging

from app.core.sms import ConsoleSmsProvider


async def test_console_sms_provider_logs_code_at_info(caplog):
    """Dev-провайдер обязан выводить OTP-код в лог уровня INFO — иначе в dev негде взять код."""
    with caplog.at_level(logging.INFO, logger="app.core.sms"):
        await ConsoleSmsProvider().send_otp("+79990000001", "123456")

    messages = [r.getMessage() for r in caplog.records if r.levelno == logging.INFO]
    assert any("+79990000001" in m and "123456" in m for m in messages)
