"""Регистрация организации — заявка с реквизитами, до подтверждения админом кабинет заблокирован."""

VALID_APPLICATION = {
    "name": "ООО Гранд Холл",
    "description": "Банкетный зал",
    "inn": "7707083893",
    "ogrn": "1027700132195",
    "address": "Москва, Тверская, 1",
    "lat": 55.7558,
    "lon": 37.6173,
    "contact_phone": "+79051234567",
    "contact_name": "Марина Кузнецова",
    "contact_email": "manager@example.com",
    "contact_position": "Управляющий",
}


async def test_application_creates_pending_company_with_requisites(client, login_user):
    owner = await login_user("+79052220001")

    resp = await client.post("/api/v1/companies", json=VALID_APPLICATION, headers=owner["headers"])

    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["status"] == "pending"
    assert body["address"] == "Москва, Тверская, 1"
    assert body["lat"] == 55.7558

    my = await client.get("/api/v1/companies/my", headers=owner["headers"])
    assert my.json()[0]["company"]["status"] == "pending"


async def test_invalid_inn_rejected(client, login_user):
    owner = await login_user("+79052220002")

    for inn in ("7707083894", "123", "770708389x", "77070838930001"):
        resp = await client.post(
            "/api/v1/companies", json={**VALID_APPLICATION, "inn": inn}, headers=owner["headers"]
        )
        assert resp.status_code == 422, (inn, resp.text)


async def test_invalid_ogrn_rejected(client, login_user):
    owner = await login_user("+79052220003")

    for ogrn in ("1027700132196", "10277", "102770013219x"):
        resp = await client.post(
            "/api/v1/companies", json={**VALID_APPLICATION, "ogrn": ogrn}, headers=owner["headers"]
        )
        assert resp.status_code == 422, (ogrn, resp.text)


async def test_application_without_map_point_rejected(client, login_user):
    owner = await login_user("+79052220004")

    payload = {k: v for k, v in VALID_APPLICATION.items() if k not in ("lat", "lon")}
    resp = await client.post("/api/v1/companies", json=payload, headers=owner["headers"])

    assert resp.status_code == 422


async def test_pending_company_is_fully_blocked(client, login_user):
    owner = await login_user("+79052220005")
    company_uuid = (
        await client.post("/api/v1/companies", json=VALID_APPLICATION, headers=owner["headers"])
    ).json()["company_uuid"]

    # любые действия кабинета — 403 до подтверждения админом
    filial = await client.post(
        f"/api/v1/companies/{company_uuid}/filials",
        json={"name": "Филиал", "address": "Адрес, 1"},
        headers=owner["headers"],
    )
    assert filial.status_code == 403
    assert "провер" in filial.json()["detail"].lower()

    assert (
        await client.patch(
            f"/api/v1/companies/{company_uuid}", json={"name": "Новое имя"}, headers=owner["headers"]
        )
    ).status_code == 403
    assert (
        await client.get(f"/api/v1/companies/{company_uuid}/team", headers=owner["headers"])
    ).status_code == 403

    # а свою заявку видеть можно
    my = await client.get("/api/v1/companies/my", headers=owner["headers"])
    assert my.status_code == 200
    assert my.json()[0]["company"]["status"] == "pending"
