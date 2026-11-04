import secrets

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.core.config import get_settings
from app.db.session import get_db

internal_api_key_header = APIKeyHeader(
    name="X-API-Key",
    scheme_name="InternalAPIKey",
    auto_error=False,
)


def require_internal_api_key(
    provided_key: str | None = Security(internal_api_key_header),
) -> None:
    configured_key = get_settings().internal_api_key
    if configured_key is None or not configured_key.get_secret_value():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Internal API key is not configured.",
        )
    if provided_key is None or not secrets.compare_digest(
        provided_key,
        configured_key.get_secret_value(),
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
            headers={"WWW-Authenticate": "ApiKey"},
        )


__all__ = ["get_db", "require_internal_api_key"]
