VACANCY_FEE_KOP = 99_000  # 990 ₽ из конфига (skill money-ledger)


async def setup_company(client, login_user, phone: str) -> dict:
    owner = await login_user(phone)
    resp = await client.post("/api/v1/companies", json={"name": "Гранд Холл «Метрополь»"}, headers=owner["headers"])
    company_uuid = resp.json()["company_uuid"]
    resp = await client.post(
        f"/api/v1/companies/{company_uuid}/filials",
        json={"name": "Гранд Холл — Тверская", "address": "Тверская, 9", "lat": 55.76, "lon": 37.61},
        headers=owner["headers"],
    )
    assert resp.status_code == 201, resp.text
    return {"owner": owner, "company_uuid": company_uuid, "filial_uuid": resp.json()["filial_uuid"]}


async def fund_company(client, login_user, make_admin, ctx, phone: str, amount_kop: int = 500_000) -> None:
    """Реальное пополнение: пруф → заявка → подтверждение админом."""
    admin = await login_user(phone)
    await make_admin(admin["me"]["user_uuid"])
    resp = await client.post(
        "/api/v1/documents",
        data={"kind": "payment_proof"},
        files={"file": ("proof.jpg", b"proof-bytes", "image/jpeg")},
        headers=ctx["owner"]["headers"],
    )
    proof_uuid = resp.json()["document_uuid"]
    resp = await client.post(
        f"/api/v1/companies/{ctx['company_uuid']}/topup-requests",
        json={"amount_kop": amount_kop, "proof_document_uuid": proof_uuid},
        headers=ctx["owner"]["headers"],
    )
    topup_uuid = resp.json()["topup_request_uuid"]
    resp = await client.post(
        f"/api/v1/admin/topup-requests/{topup_uuid}/resolve",
        json={"action": "approve"},
        headers=admin["headers"],
    )
    assert resp.status_code == 200, resp.text
    ctx["admin"] = admin


def vacancy_payload(ctx, **overrides) -> dict:
    payload = {
        "filial_uuid": ctx["filial_uuid"],
        "role_name": "Официант",
        "event_title": "Свадебный банкет",
        "starts_at": "2026-07-12T16:00:00+03:00",
        "ends_at": "2026-07-12T23:00:00+03:00",
        "venue_address": "Тверская, 9",
        "lat": 55.76,
        "lon": 37.61,
        "pay_hour_kop": 45_000,
        "slots": 12,
        "urgent": True,
        "tags": ["Банкет", "Свадьба"],
        "requirements": ["Опыт от 6 мес", "Чёрный верх / низ", "Медкнижка"],
    }
    payload.update(overrides)
    return payload


async def create_draft(client, ctx, **overrides) -> dict:
    resp = await client.post(
        f"/api/v1/companies/{ctx['company_uuid']}/vacancies",
        json=vacancy_payload(ctx, **overrides),
        headers=ctx["owner"]["headers"],
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def publish(client, ctx, vacancy_uuid: str):
    return await client.post(f"/api/v1/vacancies/{vacancy_uuid}/publish", headers=ctx["owner"]["headers"])


async def moderate(client, ctx, vacancy_uuid: str, action: str, reason: str | None = None):
    return await client.post(
        f"/api/v1/admin/vacancies/{vacancy_uuid}/moderate",
        json={"action": action, "reason": reason},
        headers=ctx["admin"]["headers"],
    )


async def test_create_draft_and_total_computed(client, login_user):
    ctx = await setup_company(client, login_user, "+79051270001")

    vacancy = await create_draft(client, ctx)

    assert vacancy["status"] == "draft"
    assert vacancy["pay_hour_kop"] == 45_000
    # 7 часов × 450 ₽/час = 3 150 ₽
    assert vacancy["pay_total_kop"] == 315_000
    assert vacancy["tags"] == ["Банкет", "Свадьба"]


async def test_create_requires_perm_create(client, login_user, add_team_member):
    ctx = await setup_company(client, login_user, "+79051270010")
    staff = await login_user("+79051270012")
    await add_team_member(ctx["company_uuid"], staff["me"]["user_uuid"], role="staff")

    resp = await client.post(
        f"/api/v1/companies/{ctx['company_uuid']}/vacancies",
        json=vacancy_payload(ctx),
        headers=staff["headers"],
    )
    assert resp.status_code == 403


async def test_foreign_filial_rejected(client, login_user):
    ctx = await setup_company(client, login_user, "+79051270020")
    other = await setup_company(client, login_user, "+79051270022")

    resp = await client.post(
        f"/api/v1/companies/{ctx['company_uuid']}/vacancies",
        json=vacancy_payload(ctx, filial_uuid=other["filial_uuid"]),
        headers=ctx["owner"]["headers"],
    )
    assert resp.status_code == 404


async def test_publish_charges_fee_and_goes_to_moderation(client, login_user, make_admin):
    ctx = await setup_company(client, login_user, "+79051270030")
    await fund_company(client, login_user, make_admin, ctx, "+79051270032")
    vacancy = await create_draft(client, ctx)

    resp = await publish(client, ctx, vacancy["vacancy_uuid"])
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "pending_moderation"

    account = (
        await client.get(f"/api/v1/companies/{ctx['company_uuid']}/account", headers=ctx["owner"]["headers"])
    ).json()
    assert account["available_kop"] == 500_000 - VACANCY_FEE_KOP

    ops = (
        await client.get(
            f"/api/v1/companies/{ctx['company_uuid']}/account/operations", headers=ctx["owner"]["headers"]
        )
    ).json()
    assert ops[0]["kind"] == "vacancy_fee"
    assert ops[0]["amount_kop"] == VACANCY_FEE_KOP
    assert ops[0]["direction"] == "out"

    # повторная публикация — 409, деньги не списываются дважды
    assert (await publish(client, ctx, vacancy["vacancy_uuid"])).status_code == 409
    account = (
        await client.get(f"/api/v1/companies/{ctx['company_uuid']}/account", headers=ctx["owner"]["headers"])
    ).json()
    assert account["available_kop"] == 500_000 - VACANCY_FEE_KOP


async def test_publish_without_funds_keeps_draft(client, login_user):
    ctx = await setup_company(client, login_user, "+79051270040")
    vacancy = await create_draft(client, ctx)

    resp = await publish(client, ctx, vacancy["vacancy_uuid"])
    assert resp.status_code == 409

    detail = (await client.get(f"/api/v1/vacancies/{vacancy['vacancy_uuid']}")).json()
    assert detail["status"] == "draft"

    ops = (
        await client.get(
            f"/api/v1/companies/{ctx['company_uuid']}/account/operations", headers=ctx["owner"]["headers"]
        )
    ).json()
    assert ops == []


async def test_moderation_approve_puts_vacancy_to_feed(client, login_user, make_admin):
    ctx = await setup_company(client, login_user, "+79051270050")
    await fund_company(client, login_user, make_admin, ctx, "+79051270052")
    vacancy = await create_draft(client, ctx)
    await publish(client, ctx, vacancy["vacancy_uuid"])

    # до одобрения лента пуста (real-data-only: пусто = [])
    assert (await client.get("/api/v1/vacancies")).json() == []

    resp = await moderate(client, ctx, vacancy["vacancy_uuid"], "approve")
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "active"

    feed = (await client.get("/api/v1/vacancies")).json()
    assert [v["vacancy_uuid"] for v in feed] == [vacancy["vacancy_uuid"]]
    assert feed[0]["company_name"] == "Гранд Холл «Метрополь»"


async def test_moderation_reject_keeps_out_of_feed(client, login_user, make_admin):
    ctx = await setup_company(client, login_user, "+79051270060")
    await fund_company(client, login_user, make_admin, ctx, "+79051270062")
    vacancy = await create_draft(client, ctx)
    await publish(client, ctx, vacancy["vacancy_uuid"])

    resp = await moderate(client, ctx, vacancy["vacancy_uuid"], "reject", "Недостаточно данных о событии")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "rejected"
    assert body["reject_reason"] == "Недостаточно данных о событии"

    assert (await client.get("/api/v1/vacancies")).json() == []


async def test_moderation_requires_admin_and_pending_status(client, login_user, make_admin):
    ctx = await setup_company(client, login_user, "+79051270070")
    await fund_company(client, login_user, make_admin, ctx, "+79051270072")
    vacancy = await create_draft(client, ctx)

    # черновик модерировать нельзя
    resp = await moderate(client, ctx, vacancy["vacancy_uuid"], "approve")
    assert resp.status_code == 409

    # не-админ не модерирует
    resp = await client.post(
        f"/api/v1/admin/vacancies/{vacancy['vacancy_uuid']}/moderate",
        json={"action": "approve"},
        headers=ctx["owner"]["headers"],
    )
    assert resp.status_code == 403


async def test_feed_filters_by_role(client, login_user, make_admin):
    ctx = await setup_company(client, login_user, "+79051270080")
    await fund_company(client, login_user, make_admin, ctx, "+79051270082")
    waiter = await create_draft(client, ctx, role_name="Официант")
    barista = await create_draft(client, ctx, role_name="Бариста", event_title="Фуршет")
    for v in (waiter, barista):
        await publish(client, ctx, v["vacancy_uuid"])
        await moderate(client, ctx, v["vacancy_uuid"], "approve")

    feed = (await client.get("/api/v1/vacancies", params={"role": "Бариста"})).json()
    assert [v["vacancy_uuid"] for v in feed] == [barista["vacancy_uuid"]]


async def test_patch_only_draft_and_archive(client, login_user, make_admin):
    ctx = await setup_company(client, login_user, "+79051270090")
    await fund_company(client, login_user, make_admin, ctx, "+79051270092")
    vacancy = await create_draft(client, ctx)

    resp = await client.patch(
        f"/api/v1/vacancies/{vacancy['vacancy_uuid']}",
        json={"slots": 20, "pay_hour_kop": 50_000},
        headers=ctx["owner"]["headers"],
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["slots"] == 20
    assert body["pay_total_kop"] == 350_000  # пересчитан: 7ч × 500 ₽

    await publish(client, ctx, vacancy["vacancy_uuid"])
    resp = await client.patch(
        f"/api/v1/vacancies/{vacancy['vacancy_uuid']}",
        json={"slots": 5},
        headers=ctx["owner"]["headers"],
    )
    assert resp.status_code == 409

    # архив скрывает из ленты
    await moderate(client, ctx, vacancy["vacancy_uuid"], "approve")
    resp = await client.post(
        f"/api/v1/vacancies/{vacancy['vacancy_uuid']}/archive", headers=ctx["owner"]["headers"]
    )
    assert resp.status_code == 200
    assert (await client.get("/api/v1/vacancies")).json() == []


async def test_company_vacancies_list_requires_membership(client, login_user):
    ctx = await setup_company(client, login_user, "+79051270100")
    outsider = await login_user("+79051270102")
    await create_draft(client, ctx)

    resp = await client.get(
        f"/api/v1/companies/{ctx['company_uuid']}/vacancies", headers=ctx["owner"]["headers"]
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["status"] == "draft"

    resp = await client.get(
        f"/api/v1/companies/{ctx['company_uuid']}/vacancies", headers=outsider["headers"]
    )
    assert resp.status_code == 403
