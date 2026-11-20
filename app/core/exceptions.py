"""Các lớp ngoại lệ (Exception) dùng chung toàn hệ thống."""

from fastapi import HTTPException, status


# --- Các Exception chuẩn dùng trong Services & Routers ---
class AppException(Exception):
    """Lớp cơ sở cho các lỗi nghiệp vụ."""

    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class AuthenticationError(AppException):
    def __init__(self, message: str = "Thông tin đăng nhập không hợp lệ."):
        super().__init__(message, status_code=status.HTTP_401_UNAUTHORIZED)


class PermissionDeniedError(AppException):
    def __init__(self, message: str = "Bạn không có quyền thực hiện thao tác này."):
        super().__init__(message, status_code=status.HTTP_403_FORBIDDEN)


class NotFoundError(AppException):
    def __init__(self, message: str = "Không tìm thấy dữ liệu yêu cầu."):
        super().__init__(message, status_code=status.HTTP_404_NOT_FOUND)


class DuplicateError(AppException):
    def __init__(self, message: str = "Dữ liệu đã tồn tại trong hệ thống."):
        super().__init__(message, status_code=status.HTTP_409_CONFLICT)


# --- Các HTTPException tương thích ngược với code cũ ---
class InvalidCredentialsException(HTTPException):
    def __init__(self, detail: str = "Email hoặc mật khẩu không chính xác"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class ProjectNotFoundException(HTTPException):
    def __init__(self, detail: str = "Không tìm thấy dự án"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class NotProjectMemberException(HTTPException):
    def __init__(self, detail: str = "Bạn không phải là thành viên của dự án này"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)