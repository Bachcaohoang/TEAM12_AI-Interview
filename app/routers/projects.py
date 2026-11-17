"""Router quản lý danh sách và thông tin dự án (Task 1 - Chính)."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.dependencies.auth import get_current_user
from app.dependencies.get_db import get_db
from app.models.project import Project
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate
from app.services import project as project_service

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get(
    "",
    response_model=list[ProjectRead],
    summary="Lấy danh sách dự án (Task 1 - Chính)",
)
def list_projects(
    skip: int = Query(0, ge=0, description="Số bản ghi bỏ qua"),
    limit: int = Query(20, ge=1, le=100, description="Số bản ghi tối đa trả về"),
    search: Optional[str] = Query(None, description="Tìm kiếm theo tên dự án"),
    status_filter: Optional[str] = Query(
        None, alias="status", description="Lọc theo trạng thái dự án"
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Project]:
    """
    Lấy danh sách dự án:
    - Admin/Manager: xem danh sách tất cả các dự án trong hệ thống.
    - User thông thường: xem danh sách các dự án do chính mình sở hữu.
    - Hỗ trợ phân trang bằng `skip` và `limit`.
    - Hỗ trợ tìm kiếm theo tên `search`.
    - Hỗ trợ lọc theo trạng thái `status` (ví dụ: 'in_progress', 'completed').
    """
    return project_service.get_projects(
        db,
        current_user=current_user,
        skip=skip,
        limit=limit,
        search=search,
        status=status_filter,
    )


@router.post(
    "",
    response_model=ProjectRead,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo một dự án mới",
)
def create_new_project(
    project_in: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Project:
    """Tạo dự án mới với chủ sở hữu là người dùng hiện tại."""
    return project_service.create_project(
        db, project_in=project_in, owner_id=current_user.id
    )


@router.get(
    "/{project_id}",
    response_model=ProjectRead,
    summary="Xem chi tiết một dự án theo ID",
)
def get_project_detail(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Project:
    """Lấy thông tin chi tiết một dự án."""
    project = project_service.get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy dự án với ID {project_id}",
        )
    # Kiểm tra quyền xem: nếu không phải admin/manager thì phải là chủ sở hữu
    if current_user.role not in ("admin", "manager") and project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền xem thông tin dự án này",
        )
    return project


@router.put(
    "/{project_id}",
    response_model=ProjectRead,
    summary="Cập nhật thông tin dự án",
)
def update_project_detail(
    project_id: int,
    project_in: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Project:
    """Cập nhật thông tin dự án (chỉ chủ dự án hoặc admin)."""
    project = project_service.get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy dự án với ID {project_id}",
        )
    try:
        return project_service.update_project(
            db, project=project, project_in=project_in, current_user=current_user
        )
    except PermissionDeniedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Xóa một dự án",
)
def delete_project_endpoint(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Xóa dự án (chỉ chủ dự án hoặc admin)."""
    project = project_service.get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy dự án với ID {project_id}",
        )
    try:
        project_service.delete_project(db, project=project, current_user=current_user)
    except PermissionDeniedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
