"""Router bình luận công việc."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.dependencies.auth import get_current_user
from app.dependencies.get_db import get_db
from app.models.user import User
from app.schemas.comment import (
    CommentCreate,
    CommentResponse,
    CommentUpdate,
    PaginatedCommentResponse,
)
from app.services import comment as comment_service

router = APIRouter(tags=["comments"])


@router.post(
    "/tasks/{task_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo bình luận cho công việc",
)
def create_task_comment(
    task_id: int,
    comment_in: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return comment_service.create_comment(
            db, task_id=task_id, comment_in=comment_in, current_user=current_user
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get(
    "/tasks/{task_id}/comments",
    response_model=PaginatedCommentResponse,
    summary="Danh sách bình luận của công việc (có phân trang)",
)
def list_task_comments(
    task_id: int,
    page: int = Query(1, description="Trang hiện tại (>= 1)"),
    page_size: int = Query(10, description="Số bản ghi mỗi trang (1-100)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    try:
        return comment_service.list_task_comments(
            db,
            task_id=task_id,
            current_user=current_user,
            page=page,
            page_size=page_size,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get(
    "/comments/{comment_id}",
    response_model=CommentResponse,
    summary="Xem chi tiết một bình luận",
)
def get_comment(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return comment_service.get_comment(db, comment_id=comment_id, current_user=current_user)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.put(
    "/comments/{comment_id}",
    response_model=CommentResponse,
    summary="Cập nhật bình luận (chủ sở hữu hoặc ADMIN)",
)
def update_comment(
    comment_id: int,
    comment_in: CommentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return comment_service.update_comment(
            db, comment_id=comment_id, comment_in=comment_in, current_user=current_user
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.delete(
    "/comments/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Xóa bình luận (chủ sở hữu hoặc ADMIN)",
)
def delete_comment(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    try:
        comment_service.delete_comment(db, comment_id=comment_id, current_user=current_user)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
