from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, SecretStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: SecretStr


class RefreshRequest(BaseModel):
    refresh_token: SecretStr


class SupabaseIdentity(BaseModel):
    id: UUID
    email: EmailStr | None = None
    email_confirmed_at: datetime | None = None
    user_metadata: dict[str, object] = Field(default_factory=dict)
    app_metadata: dict[str, object] = Field(default_factory=dict)

    @property
    def is_admin(self) -> bool:
        roles = self.app_metadata.get("roles", [])
        return self.app_metadata.get("role") == "admin" or (
            isinstance(roles, list) and "admin" in roles
        )


class AuthSession(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int | None = None
    expires_at: int | None = None
    user: SupabaseIdentity


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    subject: str | None = None
