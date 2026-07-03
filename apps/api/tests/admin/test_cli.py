from app.cli import grant_admin


async def test_grant_admin_sets_platform_role(client, login_user, settings):
    session = await login_user("+79054440001")

    granted = await grant_admin("+79054440001", database_url=settings.database_url)

    assert granted is True
    me = await client.get("/api/v1/users/me", headers=session["headers"])
    assert me.json()["platform_role"] == "admin"


async def test_grant_admin_unknown_phone_returns_false(settings):
    granted = await grant_admin("+79999999999", database_url=settings.database_url)

    assert granted is False
