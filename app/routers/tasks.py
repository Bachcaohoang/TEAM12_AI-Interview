"""Endpoint quản lý nhóm công việc (Task)."""

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.dependencies.auth import get_current_user
from app.dependencies.get_db import get_db
from app.models.user import User
from app.schemas.task import TaskResponse
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
