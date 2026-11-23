"""Endpoint quản lý nhóm công việc (Task)."""

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.dependencies.auth import get_current_user
from app.dependencies.get_db import get_db
from app.models.user import User
from app.schemas.task import TaskResponse, TaskStatusUpdate, TaskUpdate
from app.services import task as task_service

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/sample")
def read_sample_task() -> dict[str, str]:
    return {"id": "sample-task", "title": "Công việc mẫu"}


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Lấy chi tiết công việc theo ID",
    description="Kiểm tra người dùng thuộc dự án chứa công việc trước khi trả về dữ liệu chi tiết.",
)
def get_task_detail(
    task_id: int = Path(..., gt=0, description="ID của công việc"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskResponse:
    try:
        return task_service.get_task_by_id(
            db=db,
            task_id=task_id,
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


@router.put(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Cập nhật công việc",
)
def update_task_put(
    task_id: int = Path(..., gt=0, description="ID của công việc"),
    task_in: TaskUpdate = ...,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskResponse:
    try:
        return task_service.update_task(
            db=db,
            task_id=task_id,
            task_in=task_in,
            current_user=current_user,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.patch(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Cập nhật công việc theo ID (PATCH)",
    description="Cập nhật các trường hợp lệ được gửi lên, không ghi đè các trường không gửi lên.",
)
def update_task_endpoint(
    task_in: TaskUpdate,
    task_id: int = Path(..., gt=0, description="ID của công việc"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskResponse:
    try:
        return task_service.update_task(
            db=db,
            task_id=task_id,
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


@router.patch(
    "/{task_id}/status",
    response_model=TaskResponse,
    summary="Đổi trạng thái công việc",
)
def change_task_status(
    task_id: int = Path(..., gt=0, description="ID của công việc"),
    status_in: TaskStatusUpdate = ...,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskResponse:
    try:
        return task_service.change_task_status(
            db=db,
            task_id=task_id,
            status=status_in.status,
            current_user=current_user,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Xóa công việc theo ID",
    description="Xóa công việc (chỉ chủ dự án, quản lý dự án MANAGER/OWNER hoặc admin hệ thống).",
)
def delete_task(
    task_id: int = Path(..., gt=0, description="ID của công việc"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    try:
        task_service.delete_task(db=db, task_id=task_id, current_user=current_user)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
