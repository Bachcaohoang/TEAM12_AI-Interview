"""Dependency lấy user từ JWT và kiểm tra quyền theo role."""

from collections.abc import Callable
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import ExpiredSignatureError, JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import (
    ExpiredTokenException,
    InactiveUserException,
    InvalidTokenException,
)
from app.dependencies.get_db import get_db
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Đọc và giải mã JWT token, kiểm tra hạn dùng và trạng thái user."""
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        email: str = payload.get("sub")
        if email is None:
            raise InvalidTokenException()
    except ExpiredSignatureError:
        raise ExpiredTokenException()
    except JWTError:
        raise InvalidTokenException()

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise InvalidTokenException()
    
    # Kiểm tra tài khoản không hoạt động (Inactive user) -> HTTP 403 Forbidden
    if not user.is_active:
        raise InactiveUserException()

    return user


def require_role(*allowed_roles: str) -> Callable[..., User]:
    """Phân quyền truy cập theo Role (User / Admin)."""
    def role_guard(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn không có quyền thực hiện thao tác này",
            )
        return current_user

    return role_guard