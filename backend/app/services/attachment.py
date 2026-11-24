"""Nghiệp vụ tệp đính kèm công việc."""

import math
import os
import re
import uuid
from pathlib import Path
from typing import Any

from fastapi import UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.models.attachment import Attachment
from app.models.user import User
from app.services.activity import (
    ACTION_ATTACHMENT_DELETED,
    ACTION_ATTACHMENT_UPLOADED,
    log_activity,
)
from app.services.task import get_task_for_user

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".txt",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".csv",
    ".zip",
}
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/gif",
    "text/plain",
    "text/csv",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/zip",
    "application/x-zip-compressed",
    "application/octet-stream",
}


def _upload_root() -> Path:
    return Path(settings.UPLOAD_DIR).resolve()


def sanitize_filename(filename: str) -> str:
    name = os.path.basename(filename.replace("\\", "/")).strip()
    name = re.sub(r"[^A-Za-z0-9._-]", "_", name)
    if not name or name in {".", ".."}:
        name = "file"
    return name[:200]


def resolve_safe_path(stored_path: str) -> Path:
    root = _upload_root()
    candidate = Path(stored_path)
    if not candidate.is_absolute():
        candidate = (root / stored_path)
    resolved = candidate.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise PermissionDeniedError("Đường dẫn tệp không hợp lệ.") from exc
    return resolved


def _get_attachment_or_404(db: Session, attachment_id: int) -> Attachment:
    attachment = db.scalar(
        select(Attachment)
        .options(joinedload(Attachment.uploader), joinedload(Attachment.task))
        .where(Attachment.id == attachment_id)
    )
    if not attachment:
        raise NotFoundError(f"Không tìm thấy tệp đính kèm với ID {attachment_id}.")
    return attachment


def _can_delete_attachment(attachment: Attachment, current_user: User) -> bool:
    role = (current_user.role or "").strip().upper()
    return attachment.user_id == current_user.id or role == "ADMIN"


async def upload_attachment(
    db: Session,
    task_id: int,
    file: UploadFile,
    current_user: User,
) -> Attachment:
    task = get_task_for_user(db, task_id, current_user)
    original_name = sanitize_filename(file.filename or "file")
    extension = Path(original_name).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
        raise ValueError(f"Loại tệp '{extension or 'không xác định'}' không được phép. Cho phép: {allowed}")

    content_type = (file.content_type or "application/octet-stream").split(";")[0].strip().lower()
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise ValueError(f"Content-Type '{content_type}' không được phép.")

    payload = await file.read()
    file_size = len(payload)
    if file_size == 0:
        raise ValueError("Tệp tải lên không được rỗng.")
    if file_size > settings.MAX_UPLOAD_SIZE_BYTES:
        max_mb = settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)
        raise ValueError(f"Dung lượng tệp vượt quá giới hạn {max_mb}MB.")

    relative_dir = str(task.id)
    stored_name = f"{uuid.uuid4().hex}_{original_name}"
    relative_path = f"{relative_dir}/{stored_name}"
    dest = resolve_safe_path(relative_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(payload)

    attachment = Attachment(
        filename=original_name,
        stored_path=relative_path,
        content_type=content_type,
        file_size=file_size,
        task_id=task.id,
        user_id=current_user.id,
    )
    db.add(attachment)
    db.flush()
    log_activity(
        db,
        user_id=current_user.id,
        project_id=task.project_id,
        action=ACTION_ATTACHMENT_UPLOADED,
        entity_type="attachment",
        entity_id=attachment.id,
        description=f"Tải lên tệp '{original_name}' cho công việc '{task.title}'.",
    )
    db.commit()
    return _get_attachment_or_404(db, attachment.id)


def list_task_attachments(
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

    filters = [Attachment.task_id == task_id]
    total = db.scalar(select(func.count(Attachment.id)).where(*filters)) or 0
    offset = (page - 1) * page_size
    items = list(
        db.scalars(
            select(Attachment)
            .options(joinedload(Attachment.uploader))
            .where(*filters)
            .order_by(Attachment.created_at.desc(), Attachment.id.desc())
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


def get_attachment_for_download(
    db: Session,
    attachment_id: int,
    current_user: User,
) -> tuple[Attachment, Path]:
    attachment = _get_attachment_or_404(db, attachment_id)
    get_task_for_user(db, attachment.task_id, current_user)
    path = resolve_safe_path(attachment.stored_path)
    if not path.is_file():
        raise NotFoundError("Tệp vật lý không còn tồn tại trên máy chủ.")
    return attachment, path


def delete_physical_file(stored_path: str) -> None:
    try:
        path = resolve_safe_path(stored_path)
    except PermissionDeniedError:
        return
    if path.is_file():
        path.unlink()


def delete_attachment(db: Session, attachment_id: int, current_user: User) -> None:
    attachment = _get_attachment_or_404(db, attachment_id)
    task = get_task_for_user(db, attachment.task_id, current_user)
    if not _can_delete_attachment(attachment, current_user):
        raise PermissionDeniedError("Chỉ người tải lên hoặc ADMIN mới được xóa tệp đính kèm.")

    stored_path = attachment.stored_path
    log_activity(
        db,
        user_id=current_user.id,
        project_id=task.project_id,
        action=ACTION_ATTACHMENT_DELETED,
        entity_type="attachment",
        entity_id=attachment.id,
        description=f"Xóa tệp '{attachment.filename}' khỏi công việc '{task.title}'.",
    )
    db.delete(attachment)
    db.commit()
    delete_physical_file(stored_path)
