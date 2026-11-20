"""Cấu hình pytest dùng chung cho toàn bộ test suite."""

import os
import sys

# Thêm thư mục gốc vào sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.db.session as db_session_module
from app.core.rate_limiter import limiter
from app.db.base import Base
from app.dependencies.get_db import get_db
from app.main import app
from app.models.project import Project  # noqa: F401
from app.models.project_member import ProjectMember  # noqa: F401
from app.models.task import Task  # noqa: F401
from app.models.user import User  # noqa: F401

# Dùng file SQLite tạm để dùng chung an toàn giữa main thread và worker thread của TestClient
TEST_DB_FILE = "./test_suite.db"
TEST_DATABASE_URL = f"sqlite:///{TEST_DB_FILE}"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(
    bind=test_engine, autoflush=False, autocommit=False
)

db_session_module.engine = test_engine
db_session_module.SessionLocal = TestingSessionLocal


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_database():
    """Tạo mới cơ sở dữ liệu và reset rate limiter trước mỗi bài test."""
    Base.metadata.create_all(bind=test_engine)
    limiter.reset()
    yield
    Base.metadata.drop_all(bind=test_engine)
    limiter.reset()


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_db_file():
    """Xóa file test_suite.db sau khi chạy xong toàn bộ test suite."""
    yield
    test_engine.dispose()
    try:
        if os.path.exists(TEST_DB_FILE):
            os.remove(TEST_DB_FILE)
    except PermissionError:
        pass


@pytest.fixture
def db():
    """Cung cấp session database cho các bài test cần thao tác trực tiếp DB."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def db_session(db):
    """Alias cho fixture db."""
    return db


@pytest.fixture
def client():
    return TestClient(app)