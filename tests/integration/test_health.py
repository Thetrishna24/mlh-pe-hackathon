def test_health_returns_200(client):
    res = client.get("/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] in ("ok", "degraded")
    assert "db" in data


def test_health_json_content_type(client):
    res = client.get("/health")
    assert "application/json" in res.content_type