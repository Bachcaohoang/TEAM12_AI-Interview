"""Router bình luận công việc (Task Comments)."""

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
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

router = APIRouter(tags=["Comments"])


@router.post(
    "/tasks/{task_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo bình luận cho công việc",
    description="Thêm một bình luận mới vào công việc chỉ định. Người dùng phải là thành viên của dự án chứa công việc.",
    responses={
        201: {"description": "Tạo bình luận thành công."},
        400: {"description": "Nội dung bình luận rỗng hoặc không hợp lệ."},
        403: {"description": "Người dùng không thuộc dự án chứa công việc."},
        404: {"description": "Không tìm thấy công việc."},
    },
)
def create_task_comment(
    task_id: int = Path(..., gt=0, description="ID của công việc cần bình luận"),
    comment_in: CommentCreate = ...,
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
    status_code=status.HTTP_200_OK,
    summary="Lấy danh sách bình luận của công việc",
    description="Lấy danh sách bình luận được sắp xếp theo thời gian tạo kèm phân trang (offset/limit).",
    responses={
        200: {"description": "Lấy danh sách bình luận thành công."},
        400: {"description": "Tham số phân trang không hợp lệ."},
        403: {"description": "Người dùng không thuộc dự án chứa công việc."},
        404: {"description": "Không tìm thấy công việc."},
    },
)
def list_task_comments(
    task_id: int = Path(..., gt=0, description="ID của công việc"),
    page: int = Query(1, ge=1, description="Trang hiện tại (>= 1)"),
    page_size: int = Query(10, ge=1, le=100, description="Số bản ghi mỗi trang (1-100)"),
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
    status_code=status.HTTP_200_OK,
    summary="Xem chi tiết một bình luận",
    description="Lấy thông tin chi tiết của bình luận theo ID. Yêu cầu quyền truy cập vào dự án chứa bình luận.",
    responses={
        200: {"description": "Lấy chi tiết bình luận thành công."},
        403: {"description": "Không có quyền xem bình luận này."},
        404: {"description": "Bình luận không tồn tại."},
    },
)
def get_comment(
    comment_id: int = Path(..., gt=0, description="ID của bình luận"),
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
    status_code=status.HTTP_200_OK,
    summary="Cập nhật nội dung bình luận",
    description="Chỉnh sửa nội dung bình luận. Chỉ tác giả bình luận hoặc Admin hệ thống mới có quyền sửa.",
    responses={
        200: {"description": "Cập nhật bình luận thành công."},
        400: {"description": "Nội dung bình luận rỗng hoặc không hợp lệ."},
        403: {"description": "Không có quyền sửa bình luận của người khác."},
        404: {"description": "Bình luận không tồn tại."},
    },
)
def update_comment(
    comment_id: int = Path(..., gt=0, description="ID của bình luận cần sửa"),
    comment_in: CommentUpdate = ...,
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
    summary="Xóa bình luận",
    description="Xóa bình luận theo ID. Chỉ tác giả bình luận hoặc Admin hệ thống mới có quyền xóa.",
    responses={
        204: {"description": "Xóa bình luận thành công."},
        403: {"description": "Không có quyền xóa bình luận của người khác."},
        404: {"description": "Bình luận không tồn tại."},
    },
)
def delete_comment(
    comment_id: int = Path(..., gt=0, description="ID của bình luận cần xóa"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    try:
        comment_service.delete_comment(db, comment_id=comment_id, current_user=current_user)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
