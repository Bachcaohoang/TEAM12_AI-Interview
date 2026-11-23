"""Router quản lý người dùng và hồ sơ cá nhân."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user, require_role
from app.dependencies.get_db import get_db
from app.models.user import User
from app.schemas.user import UserProfileUpdate, UserRead
from app.services import user as user_service

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "",
    response_model=list[UserRead],
    status_code=status.HTTP_200_OK,
    summary="Lấy danh sách người dùng trong hệ thống",
    description="Truy xuất danh sách người dùng có hỗ trợ phân trang (skip, limit), tìm kiếm theo tên/email và lọc vai trò. Yêu cầu quyền ADMIN hoặc MANAGER.",
    responses={
        200: {"description": "Lấy danh sách người dùng thành công."},
        401: {"description": "Chưa đăng nhập / Token không hợp lệ."},
        403: {"description": "Không có quyền truy cập (yêu cầu quyền ADMIN hoặc MANAGER)."},
    },
)
def list_users(
    skip: int = Query(0, ge=0, description="Số bản ghi bỏ qua"),
    limit: int = Query(20, ge=1, le=100, description="Số bản ghi tối đa trả về"),
    search: Optional[str] = Query(None, description="Tìm kiếm theo email hoặc tên"),
    role: Optional[str] = Query(None, description="Lọc theo vai trò (user, manager, admin)"),
    current_user: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
) -> list[User]:
    return user_service.get_users(
        db, skip=skip, limit=limit, search=search, role=role
    )


@router.get(
    "/profile",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Xem thông tin hồ sơ của người dùng hiện tại",
    description="Trả về thông tin hồ sơ cá nhân của người dùng đang đăng nhập dựa trên JWT token.",
    responses={
        200: {"description": "Lấy thông tin hồ sơ thành công."},
        401: {"description": "Chưa đăng nhập / Token không hợp lệ."},
    },
)
def get_my_profile(
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user


@router.put(
    "/profile",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Cập nhật thông tin hồ sơ người dùng hiện tại",
    description="Cập nhật họ và tên của người dùng đang đăng nhập.",
    responses={
        200: {"description": "Cập nhật hồ sơ thành công."},
        400: {"description": "Dữ liệu cập nhật không hợp lệ."},
        401: {"description": "Chưa đăng nhập / Token không hợp lệ."},
    },
)
def update_my_profile(
    profile_in: UserProfileUpdate = ...,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    return user_service.update_user_profile(db, current_user, profile_in)


@router.get(
    "/{user_id}",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Xem thông tin chi tiết một người dùng theo ID",
    description="Xem thông tin người dùng trong hệ thống dựa trên User ID (yêu cầu đã đăng nhập).",
    responses={
        200: {"description": "Lấy thông tin người dùng thành công."},
        401: {"description": "Chưa đăng nhập / Token không hợp lệ."},
        404: {"description": "Không tìm thấy người dùng với ID chỉ định."},
    },
)
def get_user_by_id_endpoint(
    user_id: int = Path(..., gt=0, description="ID của người dùng cần xem"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    user = user_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy người dùng với ID {user_id}",
        )
    return user
