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

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get(
    "",
    response_model=NotificationListResponse,
    summary="Lấy danh sách thông báo của người dùng hiện tại",
)
def list_notifications(
    unread_only: bool = Query(False, description="Chỉ lấy thông báo chưa đọc"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
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
    summary="Đánh dấu tất cả thông báo là đã đọc",
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
    summary="Đánh dấu một thông báo là đã đọc",
)
def read_single_notification(
    notification_id: int = Path(..., gt=0, description="ID của thông báo"),
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
