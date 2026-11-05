import json
from json import JSONDecodeError
from functools import lru_cache
from pathlib import Path
from typing import Annotated

from dotenv import load_dotenv
from pydantic import AliasChoices, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import ArgumentError


# Use this Backend checkout's local service configuration consistently, even
# when the launching shell carries stale Agent credentials from another run.
load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=True)


class Settings(BaseSettings):
    app_name: str = "Life Purpose API"
    debug: bool = False
    database_url: SecretStr | None = None
    database_user: str | None = Field(
        default=None,
        validation_alias=AliasChoices("DB_USER", "user", "USER"),
    )
    database_password: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("DB_PASSWORD", "password", "PASSWORD"),
    )
    database_host: str | None = Field(
        default=None,
        validation_alias=AliasChoices("DB_HOST", "host", "HOST"),
    )
    database_port: int | None = Field(
        default=None,
        validation_alias=AliasChoices("DB_PORT", "port", "PORT"),
    )
    database_name: str | None = Field(
        default=None,
        validation_alias=AliasChoices("DB_NAME", "dbname", "DBNAME"),
    )
    supabase_url: str | None = None
    supabase_anon_key: SecretStr | None = None
    internal_api_key: SecretStr | None = None
    agent_api_url: str | None = None
    agent_api_key: SecretStr | None = None
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:5173"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> object:
        if not isinstance(value, str):
            return value

        raw_value = value.strip()
        if not raw_value:
            return []

        try:
            parsed_value = json.loads(raw_value)
        except JSONDecodeError:
            if raw_value.startswith("["):
                raise ValueError(
                    "CORS_ORIGINS must be a JSON array or comma-separated URLs.",
                ) from None
            return [origin.strip() for origin in raw_value.split(",") if origin.strip()]

        if isinstance(parsed_value, str):
            return [parsed_value]
        if isinstance(parsed_value, list) and all(
            isinstance(origin, str) for origin in parsed_value
        ):
            return parsed_value
        raise ValueError(
            "CORS_ORIGINS must be a JSON array or comma-separated URLs.",
        )

    @property
    def sqlalchemy_database_url(self) -> str:
        if self.database_url is not None:
            raw_url = self.database_url.get_secret_value()
            try:
                parsed_url = make_url(raw_url)
            except (ArgumentError, ValueError):
                parsed_url = None

            if (
                parsed_url is not None
                and parsed_url.host
                and parsed_url.port
                and parsed_url.database
                and parsed_url.username
                and parsed_url.password
            ):
                return parsed_url.set(drivername="postgresql+psycopg").render_as_string(
                    hide_password=False,
                )

        if (
            self.database_user
            and self.database_password is not None
            and self.database_host
            and self.database_port
            and self.database_name
        ):
            return URL.create(
                drivername="postgresql+psycopg",
                username=self.database_user,
                password=self.database_password.get_secret_value(),
                host=self.database_host,
                port=self.database_port,
                database=self.database_name,
                query={"sslmode": "require"},
            ).render_as_string(hide_password=False)

        raise ValueError(
            "Configure a valid DATABASE_URL or all of user, password, host, port, and dbname.",
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
