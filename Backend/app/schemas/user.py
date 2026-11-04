from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str | None = Field(default=None, max_length=200)


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=200)
    is_active: bool | None = None

    @field_validator("is_active", mode="before")
    @classmethod
    def is_active_cannot_be_null(cls, value: bool | None) -> bool | None:
        if value is None:
            raise ValueError("is_active cannot be null")
        return value


class UserRead(BaseModel):
    id: int
    email: EmailStr
    full_name: str | None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
