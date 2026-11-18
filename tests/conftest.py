"""Cấu hình Pytest fixture dùng chung cho toàn bộ test suite."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.dependencies.get_db import get_db
from app.main import app

TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    bind=test_engine, autoflush=False, autocommit=False
)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_database():
    """Tạo mới toàn bộ cấu trúc bảng trước mỗi test và drop sau khi hoàn tất."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client():
    """Client gọi API kiểm thử."""
    return TestClient(app)


@pytest.fixture
def db_session():
    """Session kết nối cơ sở dữ liệu kiểm thử."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
