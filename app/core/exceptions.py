# app/core/exceptions.py
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

def create_error_response(status_code: int, message: str, details: dict | list | None = None):
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {
                "code": status_code,
                "message": message,
                "details": details
            }
        }
    )

async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return create_error_response(
        status_code=exc.status_code,
        message=str(exc.detail)
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return create_error_response(
        status_code=status.HTTP_400_BAD_REQUEST,
        message="Dữ liệu đầu vào không hợp lệ",
        details=exc.errors()
    )

async def unhandled_exception_handler(request: Request, exc: Exception):
    return create_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message="Lỗi hệ thống nội bộ (Internal Server Error)"
    )