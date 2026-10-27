def test_cors_headers_allowed_origin(client):
    """Verify configured origin http://localhost:3000 receives CORS headers."""
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_cors_disallowed_origin(client):
    """Verify unauthorized origin does not receive access-control-allow-origin header."""
    response = client.options(
        "/health",
        headers={
            "Origin": "http://malicious-site.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.headers.get("access-control-allow-origin") is None
