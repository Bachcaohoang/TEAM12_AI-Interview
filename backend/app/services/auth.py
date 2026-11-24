"""Nghiệp vụ xác thực người dùng và quản lý token."""

from typing import Optional
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AuthenticationError, NotFoundError
from app.core.security import (
    create_access_token,
    create_password_reset_token,
    create_refresh_token,
    decode_token,
    verify_password,
    verify_password_reset_token,
)
from app.models.user import User
from app.schemas.auth import TokenResponse
from app.services.user import get_user_by_email, get_user_by_id


def authenticate_user(
    db: Session, email: str, password: str
) -> Optional[User]:
    """Kiểm tra email và mật khẩu khi đăng nhập."""
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_user_tokens(user: User) -> TokenResponse:
    """Tạo cặp Access Token và Refresh Token cho user."""
    access_token = create_access_token(subject=user.id, role=user.role)
    refresh_token = create_refresh_token(subject=user.id)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
    )


def refresh_user_tokens(db: Session, refresh_token: str) -> TokenResponse:
    """Tạo Access Token và Refresh Token mới từ refresh token hợp lệ."""
    try:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise AuthenticationError("Token không phải là refresh token hợp lệ.")
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise AuthenticationError("Refresh token không có subject.")
        user_id = int(user_id_str)
    except (JWTError, ValueError) as exc:
        raise AuthenticationError("Refresh token không hợp lệ hoặc đã hết hạn.") from exc

    user = get_user_by_id(db, user_id)
    if not user:
        raise NotFoundError("Người dùng không còn tồn tại.")
    if not user.is_active:
        raise AuthenticationError("Tài khoản người dùng đã bị vô hiệu hóa.")

    return create_user_tokens(user)


def request_password_reset(db: Session, email: str) -> str:
    """Tạo token đặt lại mật khẩu cho email yêu cầu."""
    email_clean = email.strip().lower()
    user = get_user_by_email(db, email_clean)
    if not user:
        raise NotFoundError(f"Không tìm thấy tài khoản với email '{email_clean}'.")
    return create_password_reset_token(user.email)
