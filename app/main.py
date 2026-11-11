"""Điểm khởi chạy ứng dụng và đăng ký các router."""

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.dependencies.get_db import get_db
from app.routers import auth, projects, tasks, users

app = FastAPI(title="Hệ thống quản lý dự án & AI Interview", version="0.1.0")

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(projects.router)
app.include_router(tasks.router)


@app.get("/", tags=["Health Check"])
def read_root() -> dict[str, str]:
    return {"message": "Project Management API is running"}


@app.get("/health/db", tags=["Health Check"])
def check_db_connection(db: Session = Depends(get_db)) -> dict[str, str]:
    """Endpoint kiểm tra kết nối trực tiếp đến cơ sở dữ liệu MySQL."""
    try:
        # Thực thi truy vấn nhẹ để xác nhận kết nối DB thành công
        db.execute(text("SELECT 1"))
        return {
            "status": "success",
            "database": "MySQL Connected Successfully!"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi kết nối cơ sở dữ liệu: {str(e)}"
        )