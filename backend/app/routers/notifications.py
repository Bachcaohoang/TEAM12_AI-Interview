"""Endpoint quản lý Thông báo hệ thống (Notification)."""

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.dependencies.auth import get_current_user
from app.dependencies.get_db import get_db
from app.models.user import User
from app.schemas.notification import (
    NotificationListResponse,
    NotificationReadAllResponse,
    NotificationResponse,
)
from app.services import notification as notification_service

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get(
    "",
    response_model=NotificationListResponse,
    status_code=status.HTTP_200_OK,
    summary="Lấy danh sách thông báo của người dùng",
    description="Truy xuất danh sách thông báo gửi đến người dùng hiện tại (kèm số lượng chưa đọc). Hỗ trợ lọc chỉ xem chưa đọc.",
    responses={
        200: {"description": "Lấy danh sách thông báo thành công."},
        401: {"description": "Chưa xác thực danh tính người dùng."},
    },
)
def list_notifications(
    unread_only: bool = Query(False, description="Chỉ lấy thông báo chưa đọc"),
    skip: int = Query(0, ge=0, description="Số lượng bản ghi bỏ qua"),
    limit: int = Query(50, ge=1, le=100, description="Số lượng bản ghi tối đa trả về"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationListResponse:
    items, total, unread_count = notification_service.list_user_notifications(
        db=db,
        user_id=current_user.id,
        unread_only=unread_only,
        skip=skip,
        limit=limit,
    )
    return NotificationListResponse(
        items=[NotificationResponse.model_validate(item) for item in items],
        total=total,
        unread_count=unread_count,
    )


@router.patch(
    "/read-all",
    response_model=NotificationReadAllResponse,
    status_code=status.HTTP_200_OK,
    summary="Đánh dấu tất cả thông báo là đã đọc",
    description="Cập nhật toàn bộ thông báo chưa đọc của người dùng hiện tại sang trạng thái đã đọc.",
    responses={
        200: {"description": "Đánh dấu tất cả thông báo đã đọc thành công."},
        401: {"description": "Chưa xác thực danh tính người dùng."},
    },
)
def read_all_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationReadAllResponse:
    updated_count = notification_service.mark_all_notifications_as_read(
        db=db,
        current_user=current_user,
    )
    return NotificationReadAllResponse(updated_count=updated_count)


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Đánh dấu một thông báo là đã đọc",
    description="Chuyển trạng thái một thông báo cụ thể sang đã đọc (chỉ người nhận thông báo mới có quyền).",
    responses={
        200: {"description": "Đánh dấu thông báo đã đọc thành công."},
        403: {"description": "Không có quyền đánh dấu thông báo của người khác."},
        404: {"description": "Thông báo không tồn tại."},
    },
)
def read_single_notification(
    notification_id: int = Path(..., gt=0, description="ID của thông báo cần đánh dấu đọc"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationResponse:
    try:
        notif = notification_service.mark_notification_as_read(
            db=db,
            notification_id=notification_id,
            current_user=current_user,
        )
        return NotificationResponse.model_validate(notif)
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
