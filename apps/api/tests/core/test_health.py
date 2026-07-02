async def test_health_reports_ok_for_db_and_redis(client):
    resp = await client.get("/api/v1/health")

    assert resp.status_code == 200
    body = resp.json()
    assert body == {"status": "ok", "database": "ok", "redis": "ok"}
