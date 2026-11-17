"""Ngoại lệ nghiệp vụ dùng chung, có thể được ánh xạ thành HTTP response."""


class NotFoundError(Exception):
    """Đối tượng được yêu cầu không tồn tại."""


class DuplicateError(Exception):
    """Dữ liệu đã tồn tại trong hệ thống (như email đã đăng ký)."""


class AuthenticationError(Exception):
    """Thông tin xác thực không chính xác hoặc token không hợp lệ."""


class PermissionDeniedError(Exception):
    """Không đủ quyền hạn để thực hiện thao tác."""
