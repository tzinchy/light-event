from pathlib import Path

PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"fake-image-payload" * 10


async def upload(client, headers, kind="passport", mime="image/png", content=PNG_BYTES):
    return await client.post(
        "/api/v1/documents",
        data={"kind": kind},
        files={"file": (f"{kind}.png", content, mime)},
        headers=headers,
    )


async def test_upload_creates_pending_document(client, login_user):
    session = await login_user()

    resp = await upload(client, session["headers"])

    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["kind"] == "passport"
    assert body["status"] == "pending"
    assert body["size_bytes"] == len(PNG_BYTES)
    assert body["document_uuid"]
    assert "storage_key" not in body  # ключ объекта наружу не отдаём


async def test_my_documents_lists_own_uploads(client, login_user):
    session = await login_user()
    await upload(client, session["headers"], kind="passport")
    await upload(client, session["headers"], kind="medbook")

    resp = await client.get("/api/v1/documents/my", headers=session["headers"])

    assert resp.status_code == 200
    kinds = {d["kind"] for d in resp.json()}
    assert kinds == {"passport", "medbook"}


async def test_content_is_visible_to_owner_and_admin_only(client, login_user, make_admin):
    owner = await login_user("+79051230001")
    stranger = await login_user("+79051230002")
    admin = await login_user("+79051230003")
    await make_admin(admin["me"]["user_uuid"])

    doc_uuid = (await upload(client, owner["headers"])).json()["document_uuid"]
    url = f"/api/v1/documents/{doc_uuid}/content"

    resp = await client.get(url, headers=owner["headers"])
    assert resp.status_code == 200
    assert resp.content == PNG_BYTES
    assert resp.headers["content-type"] == "image/png"

    # другой пользователь (в т.ч. любой сотрудник компании) содержимое KYC не видит
    resp = await client.get(url, headers=stranger["headers"])
    assert resp.status_code == 403

    resp = await client.get(url, headers=admin["headers"])
    assert resp.status_code == 200

    resp = await client.get(url)
    assert resp.status_code == 401


async def test_unsupported_mime_rejected(client, login_user):
    session = await login_user()

    resp = await upload(client, session["headers"], mime="text/plain")

    assert resp.status_code == 415


async def test_files_land_in_local_folder_when_backend_is_local(client, login_user, settings):
    session = await login_user()
    await upload(client, session["headers"])

    stored = [p for p in Path(settings.local_storage_path).rglob("*") if p.is_file()]
    assert any(p.read_bytes() == PNG_BYTES for p in stored)


async def test_oversized_file_rejected(client, login_user, settings):
    session = await login_user("+79051230041")
    too_big = b"\x89PNG\r\n\x1a\n" + b"x" * (settings.document_max_size_mb * 1024 * 1024 + 1)

    resp = await upload(client, session["headers"], content=too_big)

    assert resp.status_code == 413


async def test_unknown_kind_rejected(client, login_user):
    session = await login_user("+79051230042")

    resp = await upload(client, session["headers"], kind="driver_license")

    assert resp.status_code == 422


async def test_pdf_upload_accepted(client, login_user):
    session = await login_user("+79051230043")

    resp = await upload(client, session["headers"], mime="application/pdf", content=b"%PDF-1.7 test")

    assert resp.status_code == 201, resp.text
    assert resp.json()["mime"] == "application/pdf"


async def test_content_of_missing_document_returns_404(client, login_user):
    session = await login_user("+79051230044")
    missing = "019f0000-0000-7000-8000-000000000000"

    resp = await client.get(f"/api/v1/documents/{missing}/content", headers=session["headers"])

    assert resp.status_code == 404


async def test_documents_require_auth(client):
    assert (await client.get("/api/v1/documents/my")).status_code == 401
    assert (
        await client.post("/api/v1/documents", data={"kind": "passport"}, files={"file": ("a.png", b"x", "image/png")})
    ).status_code == 401
