"""Đọc cấu hình từ biến môi trường hoặc file .env."""

from typing import Optional
from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Hệ thống quản lý dự án & AI Interview"

    # Cấu hình MySQL cá nhân
    MYSQL_SERVER: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "123456"
    MYSQL_DB: str = "ai_interview_db"

    # Chuỗi kết nối DB
    DATABASE_URL: Optional[str] = None

    @computed_field
    @property
    def database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        # Fallback sang SQLite nếu không có cấu hình MySQL cụ thể trong .env
        return "sqlite:///./project_management.db"

    # Cấu hình JWT Auth
    SECRET_KEY: str = "your-super-secret-key-change-in-production-long-enough-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    RESET_TOKEN_EXPIRE_MINUTES: int = 15

    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024


    # Alias thuộc tính dạng chữ thường tương thích ngược
    @property
    def secret_key(self) -> str:
        return self.SECRET_KEY

    @property
    def algorithm(self) -> str:
        return self.ALGORITHM

    @property
    def access_token_expire_minutes(self) -> int:
        return self.ACCESS_TOKEN_EXPIRE_MINUTES

    @property
    def refresh_token_expire_days(self) -> int:
        return self.REFRESH_TOKEN_EXPIRE_DAYS

    @property
    def reset_token_expire_minutes(self) -> int:
        return self.RESET_TOKEN_EXPIRE_MINUTES

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
