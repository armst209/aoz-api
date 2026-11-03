def test_health_check(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_cors_preflight_allows_any_origin(client):
    response = client.options(
        "/api/v1/characters/",
        headers={
            "Origin": "https://example.com",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] in ("*", "https://example.com")
    assert response.headers["access-control-allow-credentials"] == "true"


def test_unknown_route_returns_404(client):
    assert client.get("/api/v1/nope").status_code == 404
