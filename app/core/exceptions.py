"""Ngoại lệ nghiệp vụ dùng chung, có thể được ánh xạ thành HTTP response."""


class NotFoundError(Exception):
    """Đối tượng được yêu cầu không tồn tại."""


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