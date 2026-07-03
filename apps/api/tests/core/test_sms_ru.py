import httpx
import pytest

from app.core.errors import DomainError
from app.core.sms import SmsRuProvider


def make_provider(handler) -> SmsRuProvider:
    transport = httpx.MockTransport(handler)
    return SmsRuProvider(api_key="test-key", client=httpx.AsyncClient(transport=transport))


async def test_sends_code_to_normalized_number():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["params"] = dict(request.url.params)
        return httpx.Response(
            200,
            json={"status": "OK", "status_code": 100, "sms": {"79309651656": {"status": "OK", "status_code": 100}}},
        )

    await make_provider(handler).send_otp("+79309651656", "123456")

    assert seen["params"]["api_id"] == "test-key"
    assert seen["params"]["to"] == "79309651656"  # sms.ru принимает номер без «+»
    assert "123456" in seen["params"]["msg"]


async def test_gateway_rejection_raises_domain_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "status": "OK",
                "status_code": 100,
                "sms": {"79309651656": {"status": "ERROR", "status_code": 207, "status_text": "Нет маршрута"}},
            },
        )

    with pytest.raises(DomainError) as exc:
        await make_provider(handler).send_otp("+79309651656", "123456")

    assert exc.value.status_code == 502


async def test_transport_failure_raises_domain_error():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("шлюз недоступен")

    with pytest.raises(DomainError) as exc:
        await make_provider(handler).send_otp("+79309651656", "123456")

    assert exc.value.status_code == 502
