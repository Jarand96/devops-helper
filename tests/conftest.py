import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, AsyncMock

# Use in-memory SQLite for all tests
SQLITE_URL = "sqlite://"

# Patch config values before the app and its dependencies are imported
_config_patches = {
    "backend.config.DATABASE_URL": SQLITE_URL,
    "backend.config.PAYMENT_API_KEY": "test-api-key",
    "backend.config.WEBHOOK_SECRET": "test-webhook-secret",
    "backend.config.INTERNAL_API_ENDPOINT": "http://internal-api.test",
    "backend.config.INTERNAL_API_TOKEN": "test-internal-token",
}

for target, value in _config_patches.items():
    patch(target, value).start()

from backend.models import Base  # noqa: E402
from backend.database import get_db  # noqa: E402
from backend.main import app  # noqa: E402


@pytest.fixture(scope="session")
def engine():
    eng = create_engine(
        SQLITE_URL,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=eng)
    yield eng
    Base.metadata.drop_all(bind=eng)


@pytest.fixture()
def db_session(engine):
    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
