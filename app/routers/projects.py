"""Endpoint cho nhóm dự án."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.dependencies.auth import get_current_user
from app.dependencies.get_db import get_db
from app.models.project import Project
from app.models.task import Task
from app.models.user import User
from app.schemas.project import (
    ProjectCreate,
    ProjectMemberAdd,
    ProjectMemberItemResponse,
    ProjectMemberResponse,
    ProjectRead,
    ProjectUpdate,
    ProjectDashboardResponse
)
from app.schemas.task import PaginatedTaskResponse, ProjectTaskCreate, TaskResponse
from app.services import project as project_service
from app.services import task as task_service

router = APIRouter(prefix="/projects", tags=["projects"])


def get_owned_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Project:
    """Dependency kiểm tra project tồn tại và current_user là chủ dự án (hoặc admin)."""
    project = project_service.get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy dự án với ID {project_id}",
        )
    if current_user.role != "admin" and project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ chủ sở hữu dự án mới có quyền thực hiện thao tác này",
        )
    return project


@router.get(
    "",
    response_model=list[ProjectRead],
    summary="Lấy danh sách dự án",
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
    summary="Cập nhật thông tin dự án",
)
def update_project_detail(
    project_id: int,
    project_in: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Project:
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


@router.get(
    "/{project_id}/tasks",
    response_model=PaginatedTaskResponse,
    tags=["tasks"],
    summary="Lấy danh sách công việc trong dự án có hỗ trợ Search, Filter, Sort và Pagination",
)
def list_project_tasks(
    project_id: int,
    search: Optional[str] = Query(
        None, description="Tìm kiếm theo tiêu đề công việc (không phân biệt hoa thường)"
    ),
    status_filter: Optional[str] = Query(
        None, alias="status", description="Lọc theo trạng thái: TODO, IN_PROGRESS, DONE"
    ),
    priority: Optional[str] = Query(
        None, description="Lọc theo mức độ ưu tiên: LOW, MEDIUM, HIGH"
    ),
    assignee_id: Optional[int] = Query(
        None, description="Lọc theo ID người được giao việc"
    ),
    page: int = Query(1, description="Trang hiện tại (mặc định là 1, >= 1)"),
    page_size: int = Query(10, description="Số lượng bản ghi mỗi trang (mặc định là 10, tối đa 100)"),
    sort_by: str = Query(
        "created_at", description="Trường cần sắp xếp: created_at, updated_at, title, status, priority"
    ),
    sort_order: str = Query("desc", description="Chiều sắp xếp: asc (tăng dần) hoặc desc (giảm dần)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    try:
        return task_service.get_project_tasks(
            db=db,
            project_id=project_id,
            current_user=current_user,
            search=search,
            status=status_filter,
            priority=priority,
            assignee_id=assignee_id,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
        )
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except PermissionDeniedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post(
    "/{project_id}/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["tasks"],
    summary="Tạo công việc mới trong dự án (thành viên dự án có quyền tạo)",
)
def create_project_task_endpoint(
    project_id: int,
    task_in: ProjectTaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Task:
    try:
        return task_service.create_project_task(
            db=db,
            project_id=project_id,
            task_in=task_in,
            current_user=current_user,
        )
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except PermissionDeniedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get(
    "/{project_id}/members",
    response_model=list[ProjectMemberItemResponse],
    status_code=status.HTTP_200_OK,
    summary="Lấy danh sách thành viên và role trong dự án",
)
def list_project_members(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    try:
        return project_service.get_project_members(
            db=db,
            project_id=project_id,
            current_user=current_user,
        )
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
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


    

@router.get(
    "/{project_id}/dashboard",
    response_model=ProjectDashboardResponse,
    status_code=status.HTTP_200_OK,
    summary="Thống kê tỷ lệ hoàn thành và số lượng task theo trạng thái/assignee",
)
def get_project_dashboard_endpoint(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    try:
        return project_service.get_project_dashboard(
            db=db,
            project_id=project_id,
            current_user=current_user,
        )
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except PermissionDeniedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc