"""Điểm khởi chạy ứng dụng và đăng ký các router."""

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware

from app.dependencies.get_db import get_db
import app.models  # noqa: F401  # Đăng ký metadata cho create_all
from app.routers import (
    activities,
    attachments,
    auth,
    comments,
    notifications,
    projects,
    tasks,
    users,
)

tags_metadata = [
    {
        "name": "Auth",
        "description": "Xác thực người dùng, cấp phát JWT Bearer Token (Login, Register, Refresh Token, Quên/Đổi mật khẩu).",
    },
    {
        "name": "Users",
        "description": "Quản lý thông tin tài khoản người dùng, danh sách thành viên và hồ sơ cá nhân (Role Guard).",
    },
    {
        "name": "Projects",
        "description": "Quản lý vòng đời dự án (CRUD), thống kê Dashboard và quản lý thành viên dự án (Project Members).",
    },
    {
        "name": "Tasks",
        "description": "Quản lý công việc trong dự án: Tìm kiếm, lọc, phân trang, sắp xếp, chi tiết, chuyển trạng thái và xóa công việc.",
    },
    {
        "name": "Activities",
        "description": "Nhật ký hoạt động (Audit Trail) ghi lại mọi thao tác trên dự án và công việc.",
    },
    {
        "name": "Comments",
        "description": "Bình luận thảo luận theo từng công việc (Task Comments) kèm phân quyền tác giả.",
    },
    {
        "name": "Attachments",
        "description": "Quản lý tệp đính kèm công việc (Upload, xem danh sách, tải về và xóa an toàn).",
    },
    {
        "name": "Notifications",
        "description": "Hệ thống thông báo đẩy nội bộ khi được giao task, thêm vào dự án hoặc thay đổi trạng thái công việc.",
    },
    {
        "name": "Health Check",
        "description": "Kiểm tra tình trạng hoạt động của API và kết nối cơ sở dữ liệu.",
    },
]

app = FastAPI(
    title="Hệ thống Quản lý Dự án & AI Interview API",
    description="""
API Backend hoàn chỉnh xây dựng bằng **FastAPI**, **SQLAlchemy** và **MySQL/SQLite**:
* **Authentication & Authorization**: JWT token, bảo vệ chống Brute-force & Rate-limiting, phân quyền RBAC (ADMIN, OWNER, MANAGER, MEMBER).
* **Project Management**: CRUD dự án, soft-delete, thành viên dự án, dashboard thống kê tiến độ.
* **Task Management**: Tìm kiếm theo title, lọc đa tiêu chí (status, priority, assignee), phân trang offset/limit tại database, sắp xếp linh hoạt, quy trình trạng thái (Workflow Transitions).
* **Collaboration**: Nhật ký hoạt động (Activity Logs), bình luận công việc (Comments), tệp đính kèm (Attachments).
* **Notifications**: Hệ thống thông báo người dùng theo thời gian thực.
    """,
    version="1.0.0",
    openapi_tags=tags_metadata,
    contact={
        "name": "Nhóm 12 - AI Interview Project",
    },
)

# Đăng ký các router nghiệp vụ
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(projects.router)
app.include_router(tasks.router)
app.include_router(activities.router)
app.include_router(comments.router)
app.include_router(attachments.router)
app.include_router(notifications.router)


@app.get(
    "/",
    tags=["Health Check"],
    summary="Kiểm tra trạng thái máy chủ",
    description="Trả về thông báo xác nhận ứng dụng API đang hoạt động bình thường.",
    status_code=status.HTTP_200_OK,
)
def read_root() -> dict[str, str]:
    return {"message": "Project Management API is running"}


@app.get(
    "/health/db",
    tags=["Health Check"],
    summary="Kiểm tra kết nối cơ sở dữ liệu",
    description="Thực hiện câu lệnh truy vấn kiểm tra kết nối trực tiếp đến cơ sở dữ liệu.",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Kết nối cơ sở dữ liệu thành công."},
        500: {"description": "Lỗi kết nối cơ sở dữ liệu."},
    },
)
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


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)