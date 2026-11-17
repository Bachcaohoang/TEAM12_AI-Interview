"""Điểm khởi chạy ứng dụng và đăng ký các router."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.dependencies.get_db import get_db
from app.models.project import Project
from app.models.user import User
from app.routers import auth, projects, tasks, users


def init_db() -> None:
    """Tự động tạo các bảng và gieo dữ liệu tài khoản quản trị mẫu nếu chưa có."""
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        admin_user = db.query(User).filter(User.email == "admin@example.com").first()
        if not admin_user:
            admin_user = User(
                email="admin@example.com",
                full_name="Quản trị viên Hệ thống",
                hashed_password=hash_password("Admin@123456"),
                role="ADMIN",
                is_active=True,
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)

            # Thêm dự án mẫu
            sample_project = Project(
                name="Dự án Nâng cấp Hệ thống AI Interview",
                description="Hệ thống phỏng vấn thông minh và chấm điểm ứng viên tự động.",
                status="in_progress",
                owner_id=admin_user.id,
            )
            db.add(sample_project)
            db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    init_db()
    yield


app = FastAPI(
    title="Hệ thống quản lý dự án & AI Interview",
    version="0.2.0",
    description="Backend API phát triển bằng FastAPI, SQLAlchemy 2.0 và JWT Authentication.",
    lifespan=lifespan,
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(projects.router)
app.include_router(tasks.router)


@app.get("/", tags=["Health Check"])
def read_root() -> dict[str, str]:
    return {"message": "Project Management API is running"}


@app.get("/health/db", tags=["Health Check"])
def check_db_connection(db: Session = Depends(get_db)) -> dict[str, str]:
    """Endpoint kiểm tra kết nối trực tiếp đến cơ sở dữ liệu."""
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "success",
            "database": "Database Connected Successfully!",
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi kết nối cơ sở dữ liệu: {str(e)}",
        )
