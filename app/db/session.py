"""Tạo engine và session factory để truy cập MySQL."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# Khởi tạo SQLAlchemy Engine hỗ trợ MySQL với Connection Pooling
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,  # Tự động kiểm tra tính sống còn của connection trước khi dùng
    pool_size=10,        # Duy trì tối đa 10 connection
    max_overflow=20,     # Cho phép mở rộng thêm 20 connection khi truy cập cao
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)