import secrets
from typing import Annotated

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.token import SupabaseIdentity
from app.services.supabase_auth import get_supabase_user
from app.services.user_service import sync_supabase_user

internal_api_key_header = APIKeyHeader(
    name="X-API-Key",
    scheme_name="InternalAPIKey",
    auto_error=False,
)
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_identity(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
) -> SupabaseIdentity:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer access token is required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        return SupabaseIdentity.model_validate(
            get_supabase_user(credentials.credentials)
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Supabase returned an invalid user identity.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def get_current_user(
    identity: Annotated[SupabaseIdentity, Depends(get_current_identity)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    user = sync_supabase_user(db, identity)
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is disabled.",
        )
    return user


def require_admin(
    identity: Annotated[SupabaseIdentity, Depends(get_current_identity)],
    _: Annotated[User, Depends(get_current_user)],
) -> SupabaseIdentity:
    if not identity.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator role is required.",
        )
    return identity


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


__all__ = [
    "get_current_identity",
    "get_current_user",
    "get_db",
    "require_admin",
    "require_internal_api_key",
]
