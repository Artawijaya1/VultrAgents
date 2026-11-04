from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.main import app


def test_internal_routes_require_api_key(client):
    response = client.get("/api/v1/internal/policies")

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid or missing API key."}


def test_internal_routes_reject_invalid_api_key(client):
    response = client.get(
        "/api/v1/internal/policies",
        headers={"X-API-Key": "wrong-key"},
    )

    assert response.status_code == 401


def test_internal_routes_accept_configured_api_key(client):
    response = client.get(
        "/api/v1/internal/policies",
        headers={"X-API-Key": "test-internal-api-key"},
    )

    assert response.status_code == 200
    assert response.json() == {"items": []}


def test_non_internal_routes_do_not_require_agent_api_key(client):
    response = client.get("/api/v1/vendors")

    assert response.status_code == 501
    assert response.json() == {
        "detail": "GET /vendors is not implemented yet."
    }


def test_internal_routes_fail_when_api_key_is_not_configured(monkeypatch):
    monkeypatch.setattr(
        "app.api.deps.get_settings",
        lambda: SimpleNamespace(internal_api_key=None),
    )

    with TestClient(app) as client:
        response = client.get(
            "/api/v1/internal/policies",
            headers={"X-API-Key": "any-key"},
        )

    assert response.status_code == 503
    assert response.json() == {"detail": "Internal API key is not configured."}
