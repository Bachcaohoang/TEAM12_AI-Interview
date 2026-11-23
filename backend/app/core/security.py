"""Hàm băm, kiểm tra mật khẩu và tạo/xác thực JWT token."""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Băm mật khẩu dạng rõ bằng thuật toán bcrypt."""
    return password_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """So khớp mật khẩu dạng rõ với chuỗi băm."""
    return password_context.verify(plain_password, hashed_password)


def validate_password_strength(password: str) -> tuple[bool, str]:
    """Kiểm tra chính sách mật khẩu (độ dài tối thiểu 6 ký tự)."""
    if len(password) < 6:
        return False, "Mật khẩu phải có ít nhất 6 ký tự."
    return True, ""


def create_token(data: dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Tạo JWT token chung với thời gian hết hạn."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta if expires_delta else timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def create_access_token(
    subject: str | int,
    role: str = "user",
    extra_claims: Optional[dict[str, Any]] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Tạo Access Token với claim sub, role và type='access'."""
    delta = (
        expires_delta
        if expires_delta
        else timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload: dict[str, Any] = {
        "sub": str(subject),
        "role": role,
        "type": "access",
    }
    if extra_claims:
        payload.update(extra_claims)
    return create_token(payload, expires_delta=delta)


def create_refresh_token(
    subject: str | int,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Tạo Refresh Token với claim sub và type='refresh'."""
    delta = (
        expires_delta
        if expires_delta
        else timedelta(days=settings.refresh_token_expire_days)
    )
    payload: dict[str, Any] = {
        "sub": str(subject),
        "type": "refresh",
    }
    return create_token(payload, expires_delta=delta)


def create_password_reset_token(email: str) -> str:
    """Tạo Token dùng riêng cho tác vụ quên/đặt lại mật khẩu."""
    delta = timedelta(minutes=settings.reset_token_expire_minutes)
    payload: dict[str, Any] = {
        "sub": email,
        "type": "password_reset",
    }
    return create_token(payload, expires_delta=delta)


def verify_password_reset_token(token: str) -> Optional[str]:
    """Xác thực token reset mật khẩu và trả về email nếu hợp lệ."""
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        if payload.get("type") != "password_reset":
            return None
        email: Optional[str] = payload.get("sub")
        return email
    except JWTError:
        return None


def decode_token(token: str) -> dict[str, Any]:
    """Giải mã và kiểm tra JWT token."""
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
