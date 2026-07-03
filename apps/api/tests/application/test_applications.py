from tests.helpers import create_verified_company

async def setup_active_vacancy(client, login_user, make_admin, base_phone: str, slots: int = 2) -> dict:
    """Компания с деньгами и опубликованной сменой — целиком через реальное API."""
    owner = await login_user(base_phone + "1")
    admin = await login_user(base_phone + "2")
    await make_admin(admin["me"]["user_uuid"])

    company_uuid = (await create_verified_company(client, owner["headers"]))["company_uuid"]
    resp = await client.post(
        f"/api/v1/companies/{company_uuid}/filials",
        json={"name": "Тверская", "address": "Тверская, 9"},
        headers=owner["headers"],
    )
    filial_uuid = resp.json()["filial_uuid"]

    resp = await client.post(
        "/api/v1/documents",
        data={"kind": "payment_proof"},
        files={"file": ("proof.jpg", b"proof", "image/jpeg")},
        headers=owner["headers"],
    )
    resp = await client.post(
        f"/api/v1/companies/{company_uuid}/topup-requests",
        json={"amount_kop": 200_000, "proof_document_uuid": resp.json()["document_uuid"]},
        headers=owner["headers"],
    )
    await client.post(
        f"/api/v1/admin/topup-requests/{resp.json()['topup_request_uuid']}/resolve",
        json={"action": "approve"},
        headers=admin["headers"],
    )

    resp = await client.post(
        f"/api/v1/companies/{company_uuid}/vacancies",
        json={
            "filial_uuid": filial_uuid,
            "role_name": "Официант",
            "event_title": "Свадебный банкет",
            "starts_at": "2026-07-12T16:00:00+03:00",
            "ends_at": "2026-07-12T23:00:00+03:00",
            "venue_address": "Тверская, 9",
            "pay_hour_kop": 45_000,
            "slots": slots,
        },
        headers=owner["headers"],
    )
    vacancy_uuid = resp.json()["vacancy_uuid"]
    await client.post(f"/api/v1/vacancies/{vacancy_uuid}/publish", headers=owner["headers"])
    resp = await client.post(
        f"/api/v1/admin/vacancies/{vacancy_uuid}/moderate",
        json={"action": "approve"},
        headers=admin["headers"],
    )
    assert resp.json()["status"] == "active"
    return {"owner": owner, "admin": admin, "company_uuid": company_uuid, "vacancy_uuid": vacancy_uuid}


async def apply_to(client, headers, vacancy_uuid: str):
    return await client.post(f"/api/v1/vacancies/{vacancy_uuid}/applications", headers=headers)


async def test_apply_creates_review_application_with_timeline(client, login_user, make_admin):
    ctx = await setup_active_vacancy(client, login_user, make_admin, "+7905128000")
    worker = await login_user("+79051280003")

    resp = await apply_to(client, worker["headers"], ctx["vacancy_uuid"])
    assert resp.status_code == 201, resp.text
    application = resp.json()
    assert application["status"] == "review"

    my = (await client.get("/api/v1/applications/my", headers=worker["headers"])).json()
    assert len(my) == 1
    assert my[0]["vacancy"]["event_title"] == "Свадебный банкет"
    assert my[0]["company_name"] == "Гранд Холл"

    detail = (
        await client.get(f"/api/v1/applications/{application['application_uuid']}", headers=worker["headers"])
    ).json()
    assert [e["kind"] for e in detail["timeline"]] == ["applied"]


async def test_apply_only_active_and_once(client, login_user, make_admin):
    ctx = await setup_active_vacancy(client, login_user, make_admin, "+7905128010")
    worker = await login_user("+79051280103")

    assert (await apply_to(client, worker["headers"], ctx["vacancy_uuid"])).status_code == 201
    # повторно — 409
    assert (await apply_to(client, worker["headers"], ctx["vacancy_uuid"])).status_code == 409

    # на черновик откликнуться нельзя
    resp = await client.post(
        f"/api/v1/companies/{ctx['company_uuid']}/vacancies",
        json={
            "filial_uuid": (
                await client.get(
                    f"/api/v1/companies/{ctx['company_uuid']}/filials", headers=ctx["owner"]["headers"]
                )
            ).json()[0]["filial_uuid"],
            "role_name": "Бариста",
            "event_title": "Фуршет",
            "starts_at": "2026-07-13T18:00:00+03:00",
            "ends_at": "2026-07-13T22:00:00+03:00",
            "venue_address": "Пресня",
            "pay_hour_kop": 50_000,
            "slots": 1,
        },
        headers=ctx["owner"]["headers"],
    )
    draft_uuid = resp.json()["vacancy_uuid"]
    assert (await apply_to(client, worker["headers"], draft_uuid)).status_code == 409


async def test_company_view_requires_perm_hire(client, login_user, make_admin, add_team_member):
    ctx = await setup_active_vacancy(client, login_user, make_admin, "+7905128020")
    worker = await login_user("+79051280203")
    staff = await login_user("+79051280204")
    await add_team_member(ctx["company_uuid"], staff["me"]["user_uuid"], role="staff")
    await apply_to(client, worker["headers"], ctx["vacancy_uuid"])

    resp = await client.get(
        f"/api/v1/vacancies/{ctx['vacancy_uuid']}/applications", headers=ctx["owner"]["headers"]
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["user_uuid"] == worker["me"]["user_uuid"]

    assert (
        await client.get(f"/api/v1/vacancies/{ctx['vacancy_uuid']}/applications", headers=staff["headers"])
    ).status_code == 403
    assert (
        await client.get(f"/api/v1/vacancies/{ctx['vacancy_uuid']}/applications", headers=worker["headers"])
    ).status_code == 403


async def test_confirm_and_reserve(client, login_user, make_admin):
    ctx = await setup_active_vacancy(client, login_user, make_admin, "+7905128030")
    first = await login_user("+79051280303")
    second = await login_user("+79051280304")
    app1 = (await apply_to(client, first["headers"], ctx["vacancy_uuid"])).json()
    app2 = (await apply_to(client, second["headers"], ctx["vacancy_uuid"])).json()

    resp = await client.post(
        f"/api/v1/applications/{app1['application_uuid']}/status",
        json={"action": "confirm"},
        headers=ctx["owner"]["headers"],
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "confirmed"

    resp = await client.post(
        f"/api/v1/applications/{app2['application_uuid']}/status",
        json={"action": "reserve"},
        headers=ctx["owner"]["headers"],
    )
    assert resp.json()["status"] == "reserve"

    # таймлайн подтверждённого: applied + confirmed
    detail = (
        await client.get(f"/api/v1/applications/{app1['application_uuid']}", headers=first["headers"])
    ).json()
    assert [e["kind"] for e in detail["timeline"]] == ["applied", "confirmed"]

    # соискатель не меняет статус сам
    resp = await client.post(
        f"/api/v1/applications/{app2['application_uuid']}/status",
        json={"action": "confirm"},
        headers=second["headers"],
    )
    assert resp.status_code == 403


async def test_confirm_respects_slots(client, login_user, make_admin):
    ctx = await setup_active_vacancy(client, login_user, make_admin, "+7905128040", slots=1)
    first = await login_user("+79051280403")
    second = await login_user("+79051280404")
    app1 = (await apply_to(client, first["headers"], ctx["vacancy_uuid"])).json()
    app2 = (await apply_to(client, second["headers"], ctx["vacancy_uuid"])).json()

    url = "/api/v1/applications/{}/status"
    assert (
        await client.post(url.format(app1["application_uuid"]), json={"action": "confirm"}, headers=ctx["owner"]["headers"])
    ).status_code == 200
    resp = await client.post(
        url.format(app2["application_uuid"]), json={"action": "confirm"}, headers=ctx["owner"]["headers"]
    )
    assert resp.status_code == 409

    # филд filled в ленте
    feed = (await client.get("/api/v1/vacancies")).json()
    assert feed[0]["filled"] == 1


async def test_blacklist_hides_candidate_from_company(client, login_user, make_admin):
    ctx = await setup_active_vacancy(client, login_user, make_admin, "+7905128050")
    worker = await login_user("+79051280503")
    application = (await apply_to(client, worker["headers"], ctx["vacancy_uuid"])).json()

    resp = await client.put(
        f"/api/v1/companies/{ctx['company_uuid']}/candidates/{worker['me']['user_uuid']}",
        json={"list": "blacklist", "note": "Неявка на смену"},
        headers=ctx["owner"]["headers"],
    )
    assert resp.status_code == 200, resp.text

    # скрыт из списка откликов компании (фильтр в repo-слое)
    listed = (
        await client.get(f"/api/v1/vacancies/{ctx['vacancy_uuid']}/applications", headers=ctx["owner"]["headers"])
    ).json()
    assert listed == []

    # и статус его заявки компания менять не может — для неё её нет
    resp = await client.post(
        f"/api/v1/applications/{application['application_uuid']}/status",
        json={"action": "confirm"},
        headers=ctx["owner"]["headers"],
    )
    assert resp.status_code == 404

    # сам соискатель свою заявку видит
    my = (await client.get("/api/v1/applications/my", headers=worker["headers"])).json()
    assert len(my) == 1


async def test_candidate_lists_crud_and_permissions(client, login_user, make_admin, add_team_member):
    ctx = await setup_active_vacancy(client, login_user, make_admin, "+7905128060")
    worker = await login_user("+79051280603")
    staff = await login_user("+79051280604")
    await add_team_member(ctx["company_uuid"], staff["me"]["user_uuid"], role="staff")
    user_uuid = worker["me"]["user_uuid"]
    base = f"/api/v1/companies/{ctx['company_uuid']}/candidates"

    resp = await client.put(
        f"{base}/{user_uuid}", json={"list": "shortlist", "note": "Топ-1% официантов"}, headers=ctx["owner"]["headers"]
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["list"] == "shortlist"

    listed = (await client.get(base, params={"list": "shortlist"}, headers=ctx["owner"]["headers"])).json()
    assert [e["user_uuid"] for e in listed] == [user_uuid]
    assert listed[0]["note"] == "Топ-1% официантов"

    # PUT перезаписывает список (кандидат в одном списке компании)
    await client.put(f"{base}/{user_uuid}", json={"list": "reserve"}, headers=ctx["owner"]["headers"])
    assert (await client.get(base, params={"list": "shortlist"}, headers=ctx["owner"]["headers"])).json() == []
    assert len((await client.get(base, params={"list": "reserve"}, headers=ctx["owner"]["headers"])).json()) == 1

    resp = await client.delete(f"{base}/{user_uuid}", headers=ctx["owner"]["headers"])
    assert resp.status_code == 204
    assert (await client.get(base, headers=ctx["owner"]["headers"])).json() == []

    # без perm_hire — 403
    assert (await client.get(base, headers=staff["headers"])).status_code == 403
    assert (
        await client.put(f"{base}/{user_uuid}", json={"list": "shortlist"}, headers=staff["headers"])
    ).status_code == 403


async def test_company_wide_applications_list(client, login_user, make_admin):
    ctx = await setup_active_vacancy(client, login_user, make_admin, "+7905128070")
    worker = await login_user("+79051280703")
    await apply_to(client, worker["headers"], ctx["vacancy_uuid"])

    resp = await client.get(
        f"/api/v1/companies/{ctx['company_uuid']}/applications", headers=ctx["owner"]["headers"]
    )
    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) == 1
    assert rows[0]["vacancy"]["event_title"] == "Свадебный банкет"

    # чужая заявка недоступна постороннему
    outsider = await login_user("+79051280704")
    app_uuid = rows[0]["application_uuid"]
    assert (
        await client.get(f"/api/v1/applications/{app_uuid}", headers=outsider["headers"])
    ).status_code == 403
