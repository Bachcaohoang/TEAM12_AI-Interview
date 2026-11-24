"""Nghiệp vụ nhật ký hoạt động."""

import math
from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.activity import ActivityLog
from app.models.user import User

ACTION_PROJECT_CREATED = "PROJECT_CREATED"
ACTION_PROJECT_UPDATED = "PROJECT_UPDATED"
ACTION_TASK_CREATED = "TASK_CREATED"
ACTION_TASK_UPDATED = "TASK_UPDATED"
ACTION_TASK_DELETED = "TASK_DELETED"
ACTION_TASK_STATUS_CHANGED = "TASK_STATUS_CHANGED"
ACTION_COMMENT_CREATED = "COMMENT_CREATED"
ACTION_COMMENT_UPDATED = "COMMENT_UPDATED"
ACTION_COMMENT_DELETED = "COMMENT_DELETED"
ACTION_ATTACHMENT_UPLOADED = "ATTACHMENT_UPLOADED"
ACTION_ATTACHMENT_DELETED = "ATTACHMENT_DELETED"


def log_activity(
    db: Session,
    *,
    user_id: Optional[int],
    project_id: int,
    action: str,
    entity_type: str,
    entity_id: Optional[int],
    description: str,
) -> ActivityLog:
    """Ghi một bản ghi hoạt động vào session hiện tại (chưa commit)."""
    activity = ActivityLog(
        user_id=user_id,
        project_id=project_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        description=description,
    )
    db.add(activity)
    return activity


def get_project_activities(
    db: Session,
    project_id: int,
    current_user: User,
    page: int = 1,
    page_size: int = 10,
) -> dict[str, Any]:
    """Lấy lịch sử hoạt động của dự án, có phân trang và kiểm tra quyền truy cập."""
    from app.services.task import check_project_access

    check_project_access(db, project_id, current_user)

    if page < 1:
        raise ValueError("Số trang (page) phải lớn hơn hoặc bằng 1.")
    if page_size < 1 or page_size > 100:
        raise ValueError("Kích thước trang (page_size) phải nằm trong khoảng từ 1 đến 100.")

    filters = [ActivityLog.project_id == project_id]
    total = db.scalar(select(func.count(ActivityLog.id)).where(*filters)) or 0
    offset = (page - 1) * page_size
    items = list(
        db.scalars(
            select(ActivityLog)
            .options(joinedload(ActivityLog.user))
            .where(*filters)
            .order_by(ActivityLog.created_at.desc(), ActivityLog.id.desc())
            .offset(offset)
            .limit(page_size)
        )
        .unique()
        .all()
    )
    total_pages = math.ceil(total / page_size) if total > 0 else 0
    return {
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_previous": page > 1 and total > 0,
        "items": items,
    }
