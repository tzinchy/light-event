from app.cli import grant_admin


async def test_grant_admin_sets_platform_role(client, login_user, settings):
    session = await login_user("admin-cli@example.com")

    granted = await grant_admin("admin-cli@example.com", database_url=settings.database_url)

    assert granted is True
    me = await client.get("/api/v1/users/me", headers=session["headers"])
    assert me.json()["platform_role"] == "admin"


async def test_grant_admin_unknown_email_returns_false(settings):
    granted = await grant_admin("nobody@example.com", database_url=settings.database_url)

    assert granted is False
