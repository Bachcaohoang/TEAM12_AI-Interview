"""Đọc cấu hình từ biến môi trường hoặc file .env."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = (
        "mysql+pymysql://root:password@localhost:3306/project_management"
    )
    secret_key: str = "change-this-development-secret"
    algorithm: str = "HS256"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
