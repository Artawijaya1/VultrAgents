from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ItemCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    owner_id: int | None = None


class ItemUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None

    @field_validator("title", mode="before")
    @classmethod
    def title_cannot_be_null(cls, value: str | None) -> str | None:
        if value is None:
            raise ValueError("title cannot be null")
        return value


class ItemRead(BaseModel):
    id: int
    title: str
    description: str | None
    owner_id: int | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
