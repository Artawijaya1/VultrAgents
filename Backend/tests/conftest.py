import os

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://test:test@localhost:5432/test",
)
os.environ.setdefault("SUPABASE_URL", "https://supabase.test")
os.environ.setdefault("SUPABASE_ANON_KEY", "test-anon-key")
os.environ["INTERNAL_API_KEY"] = "test-internal-api-key"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_current_identity
from app.db.session import get_db
from app.main import app
from app.models import Base
from app.schemas.token import SupabaseIdentity
from app.core.config import get_settings

ADMIN_IDENTITY = SupabaseIdentity(
    id="4c9727a8-9194-4c93-a94c-2ca3fd2e0243",
    email="admin@example.com",
    app_metadata={"role": "admin"},
)

os.environ["DATABASE_URL"] = "postgresql+psycopg://test:test@localhost:5432/test"
os.environ["SUPABASE_URL"] = "https://supabase.test"
os.environ["SUPABASE_ANON_KEY"] = "test-anon-key"
os.environ["INTERNAL_API_KEY"] = "test-internal-api-key"
get_settings.cache_clear()


@pytest.fixture
def test_session_factory():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )
    Base.metadata.create_all(bind=engine)
    yield TestingSessionLocal
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def client(test_session_factory):
    def override_get_db():
        with test_session_factory() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_identity] = lambda: ADMIN_IDENTITY
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
