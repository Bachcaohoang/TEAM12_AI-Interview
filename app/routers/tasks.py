"""Endpoint quản lý công việc."""

from fastapi import APIRouter, Depends, HTTPException, status
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
    summary="Xem chi tiết công việc",
)
def get_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return task_service.get_task_for_user(db, task_id=task_id, current_user=current_user)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.put(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Cập nhật công việc",
)
def update_task(
    task_id: int,
    task_in: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return task_service.update_task(
            db, task_id=task_id, task_in=task_in, current_user=current_user
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.patch(
    "/{task_id}/status",
    response_model=TaskResponse,
    summary="Đổi trạng thái công việc",
)
def change_task_status(
    task_id: int,
    status_in: TaskStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return task_service.change_task_status(
            db, task_id=task_id, status=status_in.status, current_user=current_user
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
    summary="Xóa công việc",
)
def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    try:
        task_service.delete_task(db, task_id=task_id, current_user=current_user)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
