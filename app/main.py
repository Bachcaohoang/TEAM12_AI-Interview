"""Điểm khởi chạy ứng dụng và đăng ký các router."""

from fastapi import FastAPI, status
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.routers import auth, projects, tasks, users

app = FastAPI(title="Hệ thống quản lý dự án & công việc", version="0.1.0")

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(projects.router)
app.include_router(tasks.router)




@app.get("/", tags=["health"])
def read_root() -> dict[str, str]:
    return {"message": "Project Management API is running"}


# app/main.py
from fastapi import FastAPI, status
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import (
    http_exception_handler,
    validation_exception_handler,
    unhandled_exception_handler
)

app = FastAPI(
    title="AI Interview API",
    version="1.0.0"
)

# Đăng ký Exception Handlers
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# Endpoint Health-check
@app.get("/health", status_code=status.HTTP_200_OK, tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": "AI Interview API"
    }