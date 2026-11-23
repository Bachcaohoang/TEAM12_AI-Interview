"""Nghiệp vụ quản lý thông báo hệ thống."""

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.models.notification import Notification
from app.models.user import User


def create_notification(
    db: Session,
    *,
    user_id: int,
    notif_type: str,
    title: str,
    message: str,
    project_id: int | None = None,
    task_id: int | None = None,
) -> Notification:
    """Thêm bản ghi thông báo vào session hiện tại (commit chung với giao dịch chính)."""
    notif = Notification(
        user_id=user_id,
        type=notif_type,
        title=title,
        message=message,
        is_read=False,
        project_id=project_id,
        task_id=task_id,
    )
    db.add(notif)
    return notif


def list_user_notifications(
    db: Session,
    user_id: int,
    unread_only: bool = False,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[Notification], int, int]:
    """Lấy danh sách thông báo của người dùng kèm tổng số và số thông báo chưa đọc."""
    base_filter = [Notification.user_id == user_id]
    if unread_only:
        base_filter.append(Notification.is_read.is_(False))

    total = db.scalar(
        select(func.count()).select_from(Notification).where(*base_filter)
    ) or 0

    unread_count = db.scalar(
        select(func.count())
        .select_from(Notification)
        .where(Notification.user_id == user_id, Notification.is_read.is_(False))
    ) or 0

    items = list(
        db.scalars(
            select(Notification)
            .where(*base_filter)
            .order_by(Notification.created_at.desc(), Notification.id.desc())
            .offset(skip)
            .limit(limit)
        ).all()
    )
    return items, total, unread_count


def mark_notification_as_read(
    db: Session,
    notification_id: int,
    current_user: User,
) -> Notification:
    """Đánh dấu 1 thông báo là đã đọc (chống IDOR: chỉ chủ thông báo được thao tác)."""
    notif = db.scalar(select(Notification).where(Notification.id == notification_id))
    if not notif:
        raise NotFoundError(f"Không tìm thấy thông báo với ID {notification_id}.")

    if notif.user_id != current_user.id:
        raise PermissionDeniedError("Bạn không có quyền thao tác trên thông báo này.")

    if not notif.is_read:
        notif.is_read = True
        db.commit()
        db.refresh(notif)

    return notif


def mark_all_notifications_as_read(db: Session, current_user: User) -> int:
    """Đánh dấu tất cả thông báo chưa đọc của người dùng hiện tại là đã đọc."""
    result = db.execute(
        update(Notification)
        .where(
            Notification.user_id == current_user.id,
            Notification.is_read.is_(False),
        )
        .values(is_read=True)
    )
    db.commit()
    return result.rowcount or 0
