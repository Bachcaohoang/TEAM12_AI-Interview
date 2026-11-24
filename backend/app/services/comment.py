"""Nghiệp vụ bình luận công việc."""

import math
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.models.comment import Comment
from app.models.user import User
from app.schemas.comment import CommentCreate, CommentUpdate
from app.services.activity import (
    ACTION_COMMENT_CREATED,
    ACTION_COMMENT_DELETED,
    ACTION_COMMENT_UPDATED,
    log_activity,
)
from app.services.task import get_task_for_user


def _is_admin(user: User) -> bool:
    return (user.role or "").strip().upper() == "ADMIN"


def _ensure_comment_owner_or_admin(comment: Comment, current_user: User) -> None:
    if comment.user_id != current_user.id and not _is_admin(current_user):
        raise PermissionDeniedError("Chỉ chủ sở hữu bình luận hoặc ADMIN mới được thực hiện thao tác này.")


def _get_comment_or_404(db: Session, comment_id: int) -> Comment:
    comment = db.scalar(
        select(Comment)
        .options(joinedload(Comment.author), joinedload(Comment.task))
        .where(Comment.id == comment_id)
    )
    if not comment:
        raise NotFoundError(f"Không tìm thấy bình luận với ID {comment_id}.")
    return comment


def create_comment(
    db: Session,
    task_id: int,
    comment_in: CommentCreate,
    current_user: User,
) -> Comment:
    task = get_task_for_user(db, task_id, current_user)
    content = comment_in.content.strip()
    if not content:
        raise ValueError("Nội dung bình luận không được để trống.")

    comment = Comment(content=content, task_id=task.id, user_id=current_user.id)
    db.add(comment)
    db.flush()
    log_activity(
        db,
        user_id=current_user.id,
        project_id=task.project_id,
        action=ACTION_COMMENT_CREATED,
        entity_type="comment",
        entity_id=comment.id,
        description=f"Thêm bình luận vào công việc '{task.title}'.",
    )
    db.commit()
    return _get_comment_or_404(db, comment.id)


def list_task_comments(
    db: Session,
    task_id: int,
    current_user: User,
    page: int = 1,
    page_size: int = 10,
) -> dict[str, Any]:
    get_task_for_user(db, task_id, current_user)
    if page < 1:
        raise ValueError("Số trang (page) phải lớn hơn hoặc bằng 1.")
    if page_size < 1 or page_size > 100:
        raise ValueError("Kích thước trang (page_size) phải nằm trong khoảng từ 1 đến 100.")

    filters = [Comment.task_id == task_id]
    total = db.scalar(select(func.count(Comment.id)).where(*filters)) or 0
    offset = (page - 1) * page_size
    items = list(
        db.scalars(
            select(Comment)
            .options(joinedload(Comment.author))
            .where(*filters)
            .order_by(Comment.created_at.desc(), Comment.id.desc())
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


def get_comment(db: Session, comment_id: int, current_user: User) -> Comment:
    comment = _get_comment_or_404(db, comment_id)
    get_task_for_user(db, comment.task_id, current_user)
    return comment


def update_comment(
    db: Session,
    comment_id: int,
    comment_in: CommentUpdate,
    current_user: User,
) -> Comment:
    comment = _get_comment_or_404(db, comment_id)
    task = get_task_for_user(db, comment.task_id, current_user)
    _ensure_comment_owner_or_admin(comment, current_user)

    content = comment_in.content.strip()
    if not content:
        raise ValueError("Nội dung bình luận không được để trống.")
    comment.content = content
    log_activity(
        db,
        user_id=current_user.id,
        project_id=task.project_id,
        action=ACTION_COMMENT_UPDATED,
        entity_type="comment",
        entity_id=comment.id,
        description=f"Cập nhật bình luận trên công việc '{task.title}'.",
    )
    db.commit()
    return _get_comment_or_404(db, comment.id)


def delete_comment(db: Session, comment_id: int, current_user: User) -> None:
    comment = _get_comment_or_404(db, comment_id)
    task = get_task_for_user(db, comment.task_id, current_user)
    _ensure_comment_owner_or_admin(comment, current_user)
    log_activity(
        db,
        user_id=current_user.id,
        project_id=task.project_id,
        action=ACTION_COMMENT_DELETED,
        entity_type="comment",
        entity_id=comment.id,
        description=f"Xóa bình luận trên công việc '{task.title}'.",
    )
    db.delete(comment)
    db.commit()
