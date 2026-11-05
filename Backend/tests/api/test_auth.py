import httpx

from app.api.deps import get_current_identity
from app.core.config import Settings
from app.main import app
from app.schemas.token import SupabaseIdentity

AUTH_USER_ID = "4c9727a8-9194-4c93-a94c-2ca3fd2e0243"


def test_auth_me_creates_local_profile(client):
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 200
    assert response.json()["email"] == "admin@example.com"

    listed = client.get("/api/v1/users/")
    assert len(listed.json()) == 1


def test_supabase_profile_is_not_linked_by_email_alone(client, test_session_factory):
    from app.models.user import User

    with test_session_factory() as db:
        db.add(User(email="admin@example.com", full_name="Unlinked"))
        db.commit()

    response = client.get("/api/v1/auth/me")

    assert response.status_code == 409


def test_profile_cannot_change_account_status(client):
    response = client.patch(
        "/api/v1/users/me",
        json={"full_name": "Updated", "is_active": False},
    )

    assert response.status_code == 422


def test_users_admin_routes_forbid_non_admin(client):
    app.dependency_overrides[get_current_identity] = lambda: SupabaseIdentity(
        id="908606b9-7da1-4e8d-a5a2-f2af3423c437",
        email="person@example.com",
        app_metadata={},
    )

    response = client.get("/api/v1/users/")

    assert response.status_code == 403


def test_api_requires_bearer_token(client):
    app.dependency_overrides.pop(get_current_identity)

    response = client.get("/api/v1/items/")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_supabase_rejects_invalid_access_token(client, monkeypatch):
    app.dependency_overrides.pop(get_current_identity)

    def reject_token(*args, **kwargs):
        return httpx.Response(401, json={"message": "invalid token"})

    monkeypatch.setattr("app.services.supabase_auth.httpx.request", reject_token)
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401


def test_login_proxies_credentials_to_supabase(client, monkeypatch):
    monkeypatch.setattr(
        "app.services.supabase_auth.get_settings",
        lambda: Settings(
            supabase_url="https://supabase.test",
            supabase_anon_key="test-anon-key",
        ),
    )

    def login_response(method, url, *, headers, json, timeout):
        assert method == "POST"
        assert url.endswith("/auth/v1/token?grant_type=password")
        assert headers["apikey"] == "test-anon-key"
        assert json == {"email": "admin@example.com", "password": "secret-password"}
        return httpx.Response(
            200,
            json={
                "access_token": "access",
                "refresh_token": "refresh",
                "token_type": "bearer",
                "expires_in": 3600,
                "user": {
                    "id": AUTH_USER_ID,
                    "email": "admin@example.com",
                    "app_metadata": {"role": "admin"},
                    "user_metadata": {},
                },
            },
        )

    monkeypatch.setattr("app.services.supabase_auth.httpx.request", login_response)
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "secret-password"},
    )

    assert response.status_code == 200
    assert response.json()["access_token"] == "access"
    assert response.json()["refresh_token"] == "refresh"


def test_login_maps_supabase_server_error_to_service_unavailable(client, monkeypatch):
    monkeypatch.setattr(
        "app.services.supabase_auth.httpx.request",
        lambda *args, **kwargs: httpx.Response(500, json={"message": "upstream failure"}),
    )

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "not-a-real-password"},
    )

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Supabase authentication service is unavailable."
    }


def test_login_maps_malformed_supabase_success_to_bad_gateway(client, monkeypatch):
    monkeypatch.setattr(
        "app.services.supabase_auth.httpx.request",
        lambda *args, **kwargs: httpx.Response(200, json={"access_token": "missing-user"}),
    )

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "not-a-real-password"},
    )

    assert response.status_code == 502
    assert response.json() == {
        "detail": "Supabase authentication returned an invalid response."
    }


def test_openapi_exposes_live_auth_routes_with_bearer_security(client):
    schema = client.get("/openapi.json").json()

    assert schema["paths"]["/api/v1/auth/login"]["post"]["summary"] == "Login"
    assert schema["paths"]["/api/v1/auth/refresh"]["post"]["summary"] == "Refresh"
    assert schema["paths"]["/api/v1/users/me"]["get"]["security"] == [
        {"HTTPBearer": []}
    ]


def test_refresh_rotates_supabase_tokens(client, monkeypatch):
    def refresh_response(method, url, *, headers, json, timeout):
        assert method == "POST"
        assert url.endswith("/auth/v1/token?grant_type=refresh_token")
        assert json == {"refresh_token": "old-refresh"}
        return httpx.Response(
            200,
            json={
                "access_token": "new-access",
                "refresh_token": "new-refresh",
                "user": {
                    "id": AUTH_USER_ID,
                    "email": "admin@example.com",
                },
            },
        )

    monkeypatch.setattr("app.services.supabase_auth.httpx.request", refresh_response)
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "old-refresh"},
    )

    assert response.status_code == 200
    assert response.json()["access_token"] == "new-access"
    assert response.json()["refresh_token"] == "new-refresh"


def test_logout_revokes_supabase_session(client, monkeypatch):
    def logout_response(method, url, *, headers, json, timeout):
        assert method == "POST"
        assert url.endswith("/auth/v1/logout")
        assert headers["Authorization"] == "Bearer access"
        return httpx.Response(204)

    monkeypatch.setattr("app.services.supabase_auth.httpx.request", logout_response)
    response = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": "Bearer access"},
    )

    assert response.status_code == 204
