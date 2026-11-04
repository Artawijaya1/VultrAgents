"""Shared runtime configuration, safe defaults for local demos."""
import os
from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    demo_only: bool = os.getenv("DEMO_ONLY", "true").lower() == "true"
    database_url: str = os.getenv("DATABASE_URL", "")
    email_send_enabled: bool = os.getenv("EMAIL_SEND_ENABLED", "false").lower() == "true"

settings = Settings()
