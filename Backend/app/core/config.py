from functools import lru_cache

from pydantic import AliasChoices, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import ArgumentError


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
    cors_origins: list[str] = ["http://localhost:5173"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
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
