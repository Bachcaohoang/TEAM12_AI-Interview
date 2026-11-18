"""Cấu hình pytest dùng chung cho toàn bộ test suite."""

import os
import sys

# Thêm thư mục gốc vào sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.rate_limiter import limiter
from app.db.base import Base
from app.dependencies.get_db import get_db
from app.main import app

# Sử dụng SQLite in-memory tập trung cho toàn bộ test suite
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
    """Tạo mới cơ sở dữ liệu và reset rate limiter trước mỗi bài test."""
    Base.metadata.create_all(bind=test_engine)
    limiter.reset()
    yield
    Base.metadata.drop_all(bind=test_engine)
    limiter.reset()


@pytest.fixture
def client():
    return TestClient(app)
