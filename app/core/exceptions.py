"""Ngoại lệ nghiệp vụ dùng chung và các lỗi Auth chuyên biệt."""

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


def create_error_response(status_code: int, message: str, details: dict | list | None = None) -> JSONResponse:
    """Tạo response lỗi dạng JSON chuẩn hóa theo định dạng chung."""
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {
                "code": status_code,
                "message": message,
                "details": details,
            },
        },
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Xử lý ngoại lệ HTTP toàn hệ thống."""
    return create_error_response(
        status_code=exc.status_code,
        message=str(exc.detail),
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Xử lý lỗi validate dữ liệu đầu vào (HTTP 400)."""
    return create_error_response(
        status_code=status.HTTP_400_BAD_REQUEST,
        message="Dữ liệu đầu vào không hợp lệ",
        details=exc.errors(),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Xử lý lỗi hệ thống không xác định (HTTP 500)."""
    return create_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message="Lỗi hệ thống nội bộ (Internal Server Error)",
    )


# ==========================================
# CUSTOM EXCEPTIONS CHO AUTH & CÁC NGHIỆP VỤ
# ==========================================

class NotFoundError(Exception):
    """Đối tượng được yêu cầu không tồn tại."""
    pass


class InvalidCredentialsException(HTTPException):
    """Lỗi sai Email hoặc Mật khẩu khi đăng nhập."""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoặc mật khẩu không chính xác",
            headers={"WWW-Authenticate": "Bearer"},
        )


class InvalidTokenException(HTTPException):
    """Lỗi Token không hợp lệ hoặc sai định dạng."""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token xác thực không hợp lệ",
            headers={"WWW-Authenticate": "Bearer"},
        )


class ExpiredTokenException(HTTPException):
    """Lỗi Token đã hết hạn."""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại",
            headers={"WWW-Authenticate": "Bearer"},
        )


class InactiveUserException(HTTPException):
    """Lỗi Tài khoản đã bị vô hiệu hóa / khóa."""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản của bạn đã bị vô hiệu hóa",
        )


class EmailAlreadyExistsException(HTTPException):
    """Lỗi Đăng ký trùng Email."""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email này đã được sử dụng trên hệ thống",
        )