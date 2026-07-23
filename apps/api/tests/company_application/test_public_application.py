"""Публичная заявка на отель без учётной записи (PLAN §11.16).

Аноним шлёт заявку + документ-пруф должности → админ модерирует →
approve заводит компанию + пользователя (main_manager) + доступ по OTP.
"""

from tests.company.test_company_application import VALID_APPLICATION

PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"proof-payload" * 10


def _payload(email: str) -> dict:
    return {**VALID_APPLICATION, "contact_email": email}


async def submit(client, email: str) -> dict:
    resp = await client.post("/api/v1/company-applications", json=_payload(email))
    assert resp.status_code == 201, resp.text
    return resp.json()


async def test_anonymous_can_submit_application(client):
    body = await submit(client, "hotel1@example.com")

    assert body["status"] == "pending"
    assert body["company_application_uuid"]
    assert body["upload_token"]  # одноразовый токен для догрузки пруфа


async def test_submit_validates_inn(client):
    resp = await client.post(
        "/api/v1/company-applications", json={**_payload("hotel2@example.com"), "inn": "123"}
    )
    assert resp.status_code == 422, resp.text


async def test_attach_proof_with_token(client):
    app = await submit(client, "hotel3@example.com")

    ok = await client.post(
        f"/api/v1/company-applications/{app['company_application_uuid']}/document",
        data={"token": app["upload_token"]},
        files={"file": ("proof.png", PNG_BYTES, "image/png")},
    )
    assert ok.status_code == 200, ok.text


async def test_attach_proof_wrong_token_forbidden(client):
    app = await submit(client, "hotel4@example.com")

    bad = await client.post(
        f"/api/v1/company-applications/{app['company_application_uuid']}/document",
        data={"token": "wrong-token"},
        files={"file": ("proof.png", PNG_BYTES, "image/png")},
    )
    assert bad.status_code == 403, bad.text


async def test_admin_endpoints_require_admin(client, login_user):
    user = await login_user("+79071110001")

    assert (await client.get("/api/v1/admin/company-applications")).status_code == 401
    assert (await client.get("/api/v1/admin/company-applications", headers=user["headers"])).status_code == 403


async def test_admin_lists_and_sees_proof(client, login_user, make_admin):
    app = await submit(client, "hotel5@example.com")
    await client.post(
        f"/api/v1/company-applications/{app['company_application_uuid']}/document",
        data={"token": app["upload_token"]},
        files={"file": ("proof.png", PNG_BYTES, "image/png")},
    )
    admin = await login_user("+79071110002")
    await make_admin(admin["me"]["user_uuid"])

    listed = await client.get("/api/v1/admin/company-applications?status=pending", headers=admin["headers"])
    assert listed.status_code == 200, listed.text
    row = {a["company_application_uuid"]: a for a in listed.json()}[app["company_application_uuid"]]
    assert row["contact_email"] == "hotel5@example.com"
    assert row["has_document"] is True

    proof = await client.get(
        f"/api/v1/admin/company-applications/{app['company_application_uuid']}/document",
        headers=admin["headers"],
    )
    assert proof.status_code == 200
    assert proof.content == PNG_BYTES


async def test_approve_creates_company_and_owner(client, login_user, make_admin):
    email = "owner-hotel@example.com"
    app = await submit(client, email)
    admin = await login_user("+79071110003")
    await make_admin(admin["me"]["user_uuid"])

    resp = await client.post(
        f"/api/v1/admin/company-applications/{app['company_application_uuid']}/approve",
        headers=admin["headers"],
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "approved"
    company_uuid = resp.json()["company_uuid"]
    assert company_uuid

    # заявитель входит по OTP на свою почту и получает кабинет main_manager
    owner = await login_user(email)
    my = await client.get("/api/v1/companies/my", headers=owner["headers"])
    assert company_uuid in {m["company"]["company_uuid"] for m in my.json()}
    # кабинет уже открыт (компания verified) — можно создать филиал
    filial = await client.post(
        f"/api/v1/companies/{company_uuid}/filials",
        json={"name": "Филиал", "address": "Адрес, 1"},
        headers=owner["headers"],
    )
    assert filial.status_code == 201, filial.text


async def test_reject_with_reason(client, login_user, make_admin):
    app = await submit(client, "hotel6@example.com")
    admin = await login_user("+79071110004")
    await make_admin(admin["me"]["user_uuid"])

    resp = await client.post(
        f"/api/v1/admin/company-applications/{app['company_application_uuid']}/reject",
        json={"reason": "Документ не подтверждает должность"},
        headers=admin["headers"],
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "rejected"
