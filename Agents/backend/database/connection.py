"""Connection factory for later production repository implementation.

The MVP uses synthetic fixtures, not this engine. Do not silently switch
financial or approval workflows to a real database without access checks.
"""
from backend.config import settings

def create_engine_for_production():
    if settings.demo_only:
        raise RuntimeError("Database writes are disabled in demo mode")
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL is required")
    from sqlalchemy import create_engine
    return create_engine(settings.database_url, pool_pre_ping=True)
