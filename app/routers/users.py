"""Router quản lý người dùng và hồ sơ cá nhân."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user, require_role
from app.dependencies.get_db import get_db
from app.models.user import User
from app.schemas.user import UserProfileUpdate, UserRead
from app.services import user as user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "",
    response_model=list[UserRead],
    summary="Lấy danh sách người dùng (Task 8 - Chính) (Bảo vệ bởi Role Guard Task 7)",
)
def list_users(
    skip: int = Query(0, ge=0, description="Số bản ghi bỏ qua"),
    limit: int = Query(20, ge=1, le=100, description="Số bản ghi tối đa trả về"),
    search: Optional[str] = Query(None, description="Tìm kiếm theo email hoặc tên"),
    role: Optional[str] = Query(None, description="Lọc theo vai trò (user, manager, admin)"),
    # Yêu cầu quyền admin hoặc manager (Task 7: Role guard)
    current_user: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
) -> list[User]:
    """
    Lấy danh sách người dùng trong hệ thống:
    - Yêu cầu quyền Admin hoặc Manager (Task 7 - Role Guard)
    - Hỗ trợ phân trang bằng `skip` và `limit`
    - Hỗ trợ tìm kiếm theo `search` và lọc theo `role`
    """
    return user_service.get_users(
        db, skip=skip, limit=limit, search=search, role=role
    )


@router.get(
    "/profile",
    response_model=UserRead,
    summary="Xem thông tin hồ sơ của người dùng hiện tại (Task 4 - Chính)",
)
def get_my_profile(
    current_user: User = Depends(get_current_user),
) -> User:
    """Trả về thông tin hồ sơ cá nhân của người dùng đang đăng nhập."""
    return current_user


@router.put(
    "/profile",
    response_model=UserRead,
    summary="Cập nhật thông tin hồ sơ người dùng hiện tại (Task 4 - Chính)",
)
def update_my_profile(
    profile_in: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    """Cập nhật họ và tên của người dùng đang đăng nhập."""
    return user_service.update_user_profile(db, current_user, profile_in)


@router.get(
    "/{user_id}",
    response_model=UserRead,
    summary="Xem thông tin chi tiết một người dùng theo ID",
)
def get_user_by_id_endpoint(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    """Xem thông tin người dùng theo ID (yêu cầu đã đăng nhập)."""
    user = user_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy người dùng với ID {user_id}",
        )
    return user
