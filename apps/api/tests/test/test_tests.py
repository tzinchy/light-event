TEST_FEE_KOP = 150_000  # 1 500 ₽ из конфига


QUESTIONS = [
    {
        "text": "Гость просит заменить блюдо после подачи. Ваши действия?",
        "multi": False,
        "options": ["Отказать", "Извиниться и предложить замену", "Заменить молча", "Игнорировать"],
        "correct_indices": [1],
    },
    {
        "text": "Что проверить перед сменой? Выберите все верные варианты.",
        "multi": True,
        "options": ["Форму и бейдж", "Стоп-лист и меню", "Список аллергенов", "Гороскоп"],
        "correct_indices": [0, 1, 2],
    },
    {
        "text": "С какой стороны подавать блюда гостю?",
        "multi": False,
        "options": ["Слева", "Справа", "Сверху"],
        "correct_indices": [0],
    },
]


async def setup_company(client, login_user, make_admin, base_phone: str, fund: bool = True) -> dict:
    owner = await login_user(base_phone + "1")
    admin = await login_user(base_phone + "2")
    await make_admin(admin["me"]["user_uuid"])
    resp = await client.post("/api/v1/companies", json={"name": "Гранд Холл"}, headers=owner["headers"])
    company_uuid = resp.json()["company_uuid"]
    if fund:
        resp = await client.post(
            "/api/v1/documents",
            data={"kind": "payment_proof"},
            files={"file": ("proof.jpg", b"proof", "image/jpeg")},
            headers=owner["headers"],
        )
        resp = await client.post(
            f"/api/v1/companies/{company_uuid}/topup-requests",
            json={"amount_kop": 300_000, "proof_document_uuid": resp.json()["document_uuid"]},
            headers=owner["headers"],
        )
        await client.post(
            f"/api/v1/admin/topup-requests/{resp.json()['topup_request_uuid']}/resolve",
            json={"action": "approve"},
            headers=admin["headers"],
        )
    return {"owner": owner, "admin": admin, "company_uuid": company_uuid}


def test_payload(**overrides) -> dict:
    payload = {
        "title": "Стандарты Гранд Холл",
        "topic": "Официант",
        "min_correct": 2,
        "questions": QUESTIONS,
    }
    payload.update(overrides)
    return payload


async def create_company_test(client, ctx, approve: bool = True) -> dict:
    resp = await client.post(
        f"/api/v1/companies/{ctx['company_uuid']}/tests",
        json=test_payload(),
        headers=ctx["owner"]["headers"],
    )
    assert resp.status_code == 201, resp.text
    test = resp.json()
    if approve:
        resp = await client.post(
            f"/api/v1/admin/tests/{test['test_uuid']}/moderate",
            json={"action": "approve"},
            headers=ctx["admin"]["headers"],
        )
        assert resp.json()["status"] == "published"
    return test


async def start_attempt(client, headers, test_uuid: str):
    return await client.post(f"/api/v1/tests/{test_uuid}/attempts", headers=headers)


async def answer_all(client, headers, attempt: dict, correct: bool = True) -> None:
    for q in attempt["questions"]:
        selected = QUESTIONS[q["position"]]["correct_indices"] if correct else [len(q["options"]) - 1]
        resp = await client.post(
            f"/api/v1/attempts/{attempt['test_attempt_uuid']}/answers",
            json={"test_question_uuid": q["test_question_uuid"], "selected_indices": selected},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text


async def test_company_test_charges_fee_and_goes_to_moderation(client, login_user, make_admin):
    ctx = await setup_company(client, login_user, make_admin, "+7905129000")

    test = await create_company_test(client, ctx, approve=False)
    assert test["status"] == "pending_moderation"
    assert test["kind"] == "company"

    account = (
        await client.get(f"/api/v1/companies/{ctx['company_uuid']}/account", headers=ctx["owner"]["headers"])
    ).json()
    assert account["available_kop"] == 300_000 - TEST_FEE_KOP
    ops = (
        await client.get(
            f"/api/v1/companies/{ctx['company_uuid']}/account/operations", headers=ctx["owner"]["headers"]
        )
    ).json()
    assert ops[0]["kind"] == "test_fee"


async def test_company_test_without_funds_rolls_back(client, login_user, make_admin):
    ctx = await setup_company(client, login_user, make_admin, "+7905129010", fund=False)

    resp = await client.post(
        f"/api/v1/companies/{ctx['company_uuid']}/tests",
        json=test_payload(),
        headers=ctx["owner"]["headers"],
    )
    assert resp.status_code == 409

    # тест не создан
    worker = await login_user("+79051290103")
    listed = (await client.get("/api/v1/tests", headers=worker["headers"])).json()
    assert listed == []


async def test_admin_creates_platform_test_published(client, login_user, make_admin):
    admin = await login_user("+79051290201")
    await make_admin(admin["me"]["user_uuid"])
    user = await login_user("+79051290202")

    resp = await client.post("/api/v1/admin/tests", json=test_payload(title="Сервис на банкете"), headers=admin["headers"])
    assert resp.status_code == 201, resp.text
    assert resp.json()["status"] == "published"
    assert resp.json()["kind"] == "platform"

    # не-админ платформенный тест не создаёт
    assert (
        await client.post("/api/v1/admin/tests", json=test_payload(), headers=user["headers"])
    ).status_code == 403

    listed = (await client.get("/api/v1/tests", headers=user["headers"])).json()
    assert len(listed) == 1
    assert listed[0]["questions_count"] == 3
    assert listed[0]["my_result"] is None
    # correct_indices наружу не отдаются нигде
    assert "correct_indices" not in str(listed)


async def test_only_published_visible_and_rejected_hidden(client, login_user, make_admin):
    ctx = await setup_company(client, login_user, make_admin, "+7905129030")
    test = await create_company_test(client, ctx, approve=False)
    worker = await login_user("+79051290303")

    assert (await client.get("/api/v1/tests", headers=worker["headers"])).json() == []

    resp = await client.post(
        f"/api/v1/admin/tests/{test['test_uuid']}/moderate",
        json={"action": "reject", "reason": "Слишком мало вопросов"},
        headers=ctx["admin"]["headers"],
    )
    assert resp.json()["status"] == "rejected"
    assert (await client.get("/api/v1/tests", headers=worker["headers"])).json() == []

    # попытка по неопубликованному тесту невозможна
    assert (await start_attempt(client, worker["headers"], test["test_uuid"])).status_code == 409


async def test_attempt_pass_flow_and_result_in_list(client, login_user, make_admin):
    ctx = await setup_company(client, login_user, make_admin, "+7905129040")
    test = await create_company_test(client, ctx)
    worker = await login_user("+79051290403")

    resp = await start_attempt(client, worker["headers"], test["test_uuid"])
    assert resp.status_code == 201, resp.text
    attempt = resp.json()
    assert attempt["status"] == "in_progress"
    assert len(attempt["questions"]) == 3
    assert "correct_indices" not in str(attempt)

    await answer_all(client, worker["headers"], attempt, correct=True)
    resp = await client.post(
        f"/api/v1/attempts/{attempt['test_attempt_uuid']}/finish", headers=worker["headers"]
    )
    assert resp.status_code == 200, resp.text
    result = resp.json()
    assert result["correct_count"] == 3
    assert result["score_pct"] == 100
    assert result["passed"] is True

    listed = (await client.get("/api/v1/tests", headers=worker["headers"])).json()
    assert listed[0]["my_result"]["passed"] is True
    assert listed[0]["my_result"]["score_pct"] == 100


async def test_multi_requires_exact_match_and_fail_below_min(client, login_user, make_admin):
    ctx = await setup_company(client, login_user, make_admin, "+7905129050")
    test = await create_company_test(client, ctx)
    worker = await login_user("+79051290503")

    attempt = (await start_attempt(client, worker["headers"], test["test_uuid"])).json()
    # первый вопрос — верно; multi — частично (не засчитывается); третий — неверно
    q = {x["position"]: x for x in attempt["questions"]}
    for position, selected in [(0, [1]), (1, [0, 1]), (2, [1])]:
        await client.post(
            f"/api/v1/attempts/{attempt['test_attempt_uuid']}/answers",
            json={"test_question_uuid": q[position]["test_question_uuid"], "selected_indices": selected},
            headers=worker["headers"],
        )
    result = (
        await client.post(f"/api/v1/attempts/{attempt['test_attempt_uuid']}/finish", headers=worker["headers"])
    ).json()
    assert result["correct_count"] == 1
    assert result["score_pct"] == 33
    assert result["passed"] is False


async def test_abandon_sets_cooldown_and_blocks_new_attempt(client, login_user, make_admin):
    ctx = await setup_company(client, login_user, make_admin, "+7905129060")
    test = await create_company_test(client, ctx)
    worker = await login_user("+79051290603")

    attempt = (await start_attempt(client, worker["headers"], test["test_uuid"])).json()
    resp = await client.post(
        f"/api/v1/attempts/{attempt['test_attempt_uuid']}/abandon", headers=worker["headers"]
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "abandoned"
    assert body["score_pct"] == 0
    assert body["cooldown_until"] is not None

    # новая попытка до конца cooldown — 409, и cooldown виден в списке
    assert (await start_attempt(client, worker["headers"], test["test_uuid"])).status_code == 409
    listed = (await client.get("/api/v1/tests", headers=worker["headers"])).json()
    assert listed[0]["cooldown_until"] is not None

    # чужая попытка недоступна
    stranger = await login_user("+79051290604")
    assert (
        await client.post(f"/api/v1/attempts/{attempt['test_attempt_uuid']}/abandon", headers=stranger["headers"])
    ).status_code == 403


async def test_company_tests_listing_for_org(client, login_user, make_admin):
    ctx = await setup_company(client, login_user, make_admin, "+7905129080")
    published = await create_company_test(client, ctx)
    resp = await client.post(
        f"/api/v1/admin/tests/{(await create_company_test(client, ctx, approve=False))['test_uuid']}/moderate",
        json={"action": "reject", "reason": "Дубль"},
        headers=ctx["admin"]["headers"],
    )
    assert resp.json()["status"] == "rejected"

    # прохождение опубликованного теста двумя соискателями (один — неуспешно)
    for phone, correct in [("+79051290803", True), ("+79051290804", False)]:
        worker = await login_user(phone)
        attempt = (await start_attempt(client, worker["headers"], published["test_uuid"])).json()
        await answer_all(client, worker["headers"], attempt, correct=correct)
        await client.post(f"/api/v1/attempts/{attempt['test_attempt_uuid']}/finish", headers=worker["headers"])

    rows = (
        await client.get(f"/api/v1/companies/{ctx['company_uuid']}/tests", headers=ctx["owner"]["headers"])
    ).json()
    # компания видит все свои тесты, включая отклонённые
    by_status = {r["status"]: r for r in rows}
    assert set(by_status) == {"published", "rejected"}
    assert by_status["published"]["questions_count"] == 3
    assert by_status["published"]["passed_count"] == 1
    assert by_status["rejected"]["passed_count"] == 0
    assert "correct_indices" not in str(rows)

    # не член команды список не видит
    stranger = await login_user("+79051290805")
    resp = await client.get(
        f"/api/v1/companies/{ctx['company_uuid']}/tests", headers=stranger["headers"]
    )
    assert resp.status_code == 403


async def test_company_test_badge_in_applications(client, login_user, make_admin):
    ctx = await setup_company(client, login_user, make_admin, "+7905129070")
    test = await create_company_test(client, ctx)
    worker = await login_user("+79051290703")

    # прохождение теста компании
    attempt = (await start_attempt(client, worker["headers"], test["test_uuid"])).json()
    await answer_all(client, worker["headers"], attempt, correct=True)
    await client.post(f"/api/v1/attempts/{attempt['test_attempt_uuid']}/finish", headers=worker["headers"])

    # смена и отклик
    resp = await client.post(
        f"/api/v1/companies/{ctx['company_uuid']}/filials",
        json={"name": "Тверская", "address": "Тверская, 9"},
        headers=ctx["owner"]["headers"],
    )
    resp = await client.post(
        f"/api/v1/companies/{ctx['company_uuid']}/vacancies",
        json={
            "filial_uuid": resp.json()["filial_uuid"],
            "role_name": "Официант",
            "event_title": "Банкет",
            "starts_at": "2026-07-12T16:00:00+03:00",
            "ends_at": "2026-07-12T23:00:00+03:00",
            "venue_address": "Тверская, 9",
            "pay_hour_kop": 45_000,
            "slots": 2,
        },
        headers=ctx["owner"]["headers"],
    )
    vacancy_uuid = resp.json()["vacancy_uuid"]
    await client.post(f"/api/v1/vacancies/{vacancy_uuid}/publish", headers=ctx["owner"]["headers"])
    await client.post(
        f"/api/v1/admin/vacancies/{vacancy_uuid}/moderate",
        json={"action": "approve"},
        headers=ctx["admin"]["headers"],
    )
    await client.post(f"/api/v1/vacancies/{vacancy_uuid}/applications", headers=worker["headers"])

    rows = (
        await client.get(
            f"/api/v1/companies/{ctx['company_uuid']}/applications", headers=ctx["owner"]["headers"]
        )
    ).json()
    assert rows[0]["company_test_passed"] is True

    # кандидат без теста — бейджа нет
    other = await login_user("+79051290704")
    await client.post(f"/api/v1/vacancies/{vacancy_uuid}/applications", headers=other["headers"])
    rows = (
        await client.get(
            f"/api/v1/companies/{ctx['company_uuid']}/applications", headers=ctx["owner"]["headers"]
        )
    ).json()
    by_user = {r["user_uuid"]: r for r in rows}
    assert by_user[other["me"]["user_uuid"]]["company_test_passed"] is False
