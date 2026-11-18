"""Router quản lý danh sách và thông tin dự án (Task 1 - Chính)."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.dependencies.auth import get_current_user, get_owned_project
from app.dependencies.get_db import get_db
from app.models.project import Project
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate
from app.schemas.project_member import ProjectMemberAdd, ProjectMemberResponse
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
    project = project_service.get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy dự án với ID {project_id}",
        )
    if current_user.role not in ("admin", "manager") and project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền xem thông tin dự án này",
        )
    return project


@router.put(
    "/{project_id}",
    response_model=ProjectRead,
    summary="Cập nhật toàn bộ thông tin dự án",
)
def update_project_detail(
    project_in: ProjectUpdate,
    project: Project = Depends(get_owned_project),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Project:
    try:
        return project_service.update_project(
            db, project=project, project_in=project_in, current_user=current_user
        )
    except PermissionDeniedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc


@router.patch(
    "/{project_id}",
    response_model=ProjectRead,
    summary="Cập nhật một phần thông tin dự án",
)
def partial_update_project_detail(
    project_in: ProjectUpdate,
    project: Project = Depends(get_owned_project),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Project:
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
    project: Project = Depends(get_owned_project),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    try:
        project_service.delete_project(db, project=project, current_user=current_user)
    except PermissionDeniedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc


@router.post(
    "/{project_id}/members",
    response_model=ProjectMemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Thêm thành viên vào dự án (chỉ OWNER)",
)
def add_member_to_project(
    member_in: ProjectMemberAdd,
    project: Project = Depends(get_owned_project),
    db: Session = Depends(get_db),
) -> ProjectMemberResponse:
    try:
        return project_service.add_project_member(
            db=db,
            project=project,
            member_in=member_in,
        )
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc



@router.delete(
    "/{project_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Xóa thành viên khỏi dự án (chỉ OWNER, không được xóa OWNER)",
)
def remove_member_from_project(
    user_id: int,
    project: Project = Depends(get_owned_project),
    db: Session = Depends(get_db),
) -> None:
    try:
        project_service.remove_project_member(
            db=db,
            project=project,
            user_id=user_id,
        )
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc