"""Dependency lấy user từ JWT và kiểm tra quyền theo role."""

from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.dependencies.get_db import get_db
from app.models.project import Project
from app.models.user import User
from app.services.user import get_user_by_id

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Xác thực token JWT và trả về User hiện tại từ cơ sở dữ liệu."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token không hợp lệ hoặc đã hết hạn",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        token_type = payload.get("type")
        if token_type and token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Loại token không hợp lệ (yêu cầu access token)",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user_id_raw = payload.get("sub")
        if not user_id_raw:
            raise credentials_exception
        user_id = int(user_id_raw)
    except (JWTError, ValueError) as exc:
        raise credentials_exception from exc

    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Người dùng không tồn tại",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản người dùng đã bị vô hiệu hóa",
        )
    return user


def require_role(*allowed_roles: str) -> Callable[..., User]:
    """
    Role Guard: Kiểm tra người dùng có một trong các role được phép hay không (không phân biệt chữ hoa/thường).
    Ví dụ: require_role("admin"), require_role("admin", "manager")
    """
    normalized_allowed = [r.strip().upper() for r in allowed_roles]

    def role_guard(
        current_user: User = Depends(get_current_user),
    ) -> User:
        user_role = (current_user.role or "").strip().upper()
        if user_role not in normalized_allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Bạn không có quyền thực hiện thao tác này. Yêu cầu một trong các quyền: {', '.join(allowed_roles)}",
            )
        return current_user

    return role_guard


def get_owned_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy dự án.",
        )

    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ OWNER mới có quyền chỉnh sửa hoặc xóa dự án này.",
        )

    return project