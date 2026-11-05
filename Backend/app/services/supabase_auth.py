import httpx
from pydantic import ValidationError
from fastapi import HTTPException, status

from app.core.config import get_settings
from app.schemas.token import AuthSession


def _supabase_request(
    method: str,
    path: str,
    *,
    payload: dict[str, str] | None = None,
    access_token: str | None = None,
) -> httpx.Response:
    settings = get_settings()
    if not settings.supabase_url or settings.supabase_anon_key is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase authentication is not configured.",
        )

    headers = {
        "apikey": settings.supabase_anon_key.get_secret_value(),
        "Accept": "application/json",
    }
    if access_token is not None:
        headers["Authorization"] = f"Bearer {access_token}"

    try:
        return httpx.request(
            method,
            f"{settings.supabase_url.rstrip('/')}{path}",
            headers=headers,
            json=payload,
            timeout=8.0,
        )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase authentication service is unavailable.",
        ) from exc


def _raise_auth_error(response: httpx.Response) -> None:
    if response.status_code in {400, 401, 403}:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed. Check the credentials or token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if response.status_code == 429 or response.status_code >= 500:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase authentication service is unavailable.",
        )
    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail="Supabase authentication request failed.",
    )


def _parse_auth_session(response: httpx.Response) -> AuthSession:
    try:
        return AuthSession.model_validate(response.json())
    except (ValueError, ValidationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Supabase authentication returned an invalid response.",
        ) from exc


def login(email: str, password: str) -> AuthSession:
    response = _supabase_request(
        "POST",
        "/auth/v1/token?grant_type=password",
        payload={"email": email, "password": password},
    )
    if not response.is_success:
        _raise_auth_error(response)
    return _parse_auth_session(response)


def refresh_session(refresh_token: str) -> AuthSession:
    response = _supabase_request(
        "POST",
        "/auth/v1/token?grant_type=refresh_token",
        payload={"refresh_token": refresh_token},
    )
    if not response.is_success:
        _raise_auth_error(response)
    return _parse_auth_session(response)


def get_supabase_user(access_token: str) -> dict[str, object]:
    response = _supabase_request(
        "GET",
        "/auth/v1/user",
        access_token=access_token,
    )
    if not response.is_success:
        _raise_auth_error(response)
    return response.json()


def logout(access_token: str) -> None:
    response = _supabase_request(
        "POST",
        "/auth/v1/logout",
        access_token=access_token,
    )
    if not response.is_success:
        _raise_auth_error(response)
