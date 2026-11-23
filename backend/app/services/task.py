import math
from datetime import datetime, timezone
from typing import Any, Optional
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.task import Task
from app.models.user import User
from app.schemas.task import ProjectTaskCreate, TaskUpdate
from app.services.activity import (
    ACTION_TASK_CREATED,
    ACTION_TASK_DELETED,
    ACTION_TASK_STATUS_CHANGED,
    ACTION_TASK_UPDATED,
    log_activity,
)
from app.services.notification import create_notification

VALID_TASK_STATUSES = {"TODO", "IN_PROGRESS", "DONE"}
VALID_TASK_PRIORITIES = {"LOW", "MEDIUM", "HIGH"}
ALLOWED_STATUS_TRANSITIONS: dict[str, set[str]] = {
    "TODO": {"IN_PROGRESS"},
    "IN_PROGRESS": {"TODO", "DONE"},
    "DONE": {"IN_PROGRESS"},
}
ALLOWED_SORT_FIELDS = {"created_at", "updated_at", "title", "status", "priority", "due_date"}
VALID_SORT_ORDERS = {"asc", "desc"}


def is_user_project_member(db: Session, project: Project, user: User) -> bool:
    if user.role and user.role.strip().upper() == "ADMIN":
        return True
    if project.owner_id == user.id:
        return True

    member = db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project.id,
            ProjectMember.user_id == user.id,
        )
    )
    return member is not None


def check_project_access(db: Session, project_id: int, current_user: User) -> Project:
    project = db.scalar(
        select(Project).where(
            Project.id == project_id,
            Project.is_deleted.is_(False),
        )
    )
    if not project:
        raise NotFoundError(f"Không tìm thấy dự án với ID {project_id}.")

    if not is_user_project_member(db, project, current_user):
        raise PermissionDeniedError("Bạn không có quyền truy cập vào dự án này.")

    return project


def get_task_for_user(db: Session, task_id: int, current_user: User) -> Task:
    task = db.scalar(
        select(Task).options(joinedload(Task.assignee)).where(Task.id == task_id)
    )
    if not task:
        raise NotFoundError(f"Không tìm thấy công việc với ID {task_id}.")
    check_project_access(db, task.project_id, current_user)
    return task


get_task_by_id = get_task_for_user


def validate_project_assignee(db: Session, project: Project, assignee_id: Optional[int]) -> None:
    if assignee_id is None:
        return

    assignee = db.scalar(select(User).where(User.id == assignee_id))
    if not assignee:
        raise NotFoundError(f"Không tìm thấy người dùng được giao việc với ID {assignee_id}.")

    if not is_user_project_member(db, project, assignee):
        raise ValueError(
            f"Người dùng với ID {assignee_id} không phải là thành viên của dự án này."
        )


def validate_status_transition(current_status: str, new_status: str) -> None:
    current_clean = (current_status or "TODO").strip().upper()
    new_clean = new_status.strip().upper()

    if new_clean not in VALID_TASK_STATUSES:
        valid_str = ", ".join(sorted(VALID_TASK_STATUSES))
        raise ValueError(f"Trạng thái '{new_status}' không hợp lệ. Các giá trị hợp lệ: {valid_str}")

    if current_clean == new_clean:
        return

    allowed_next = ALLOWED_STATUS_TRANSITIONS.get(current_clean, set())
    if new_clean not in allowed_next:
        allowed_str = ", ".join(sorted(allowed_next)) if allowed_next else "không có"
        raise ValueError(
            f"Không thể chuyển trạng thái từ '{current_clean}' sang '{new_clean}'. "
            f"Các trạng thái tiếp theo hợp lệ: {allowed_str}."
        )


def validate_and_normalize_due_date(due_date: Optional[datetime]) -> Optional[datetime]:
    if due_date is None:
        return None

    if due_date.tzinfo is not None:
        due_utc = due_date.astimezone(timezone.utc).replace(tzinfo=None)
    else:
        due_utc = due_date

    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    if due_utc < now_utc:
        raise ValueError("Hạn chót (due_date) không được nằm trong quá khứ.")

    return due_utc


def get_project_tasks(
    db: Session,
    project_id: int,
    current_user: User,
    search: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    assignee_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 10,
    sort_by: str = "created_at",
    sort_order: str = "desc",
) -> dict[str, Any]:
    check_project_access(db, project_id, current_user)

    if page < 1:
        raise ValueError("Số trang (page) phải lớn hơn hoặc bằng 1.")
    if page_size < 1 or page_size > 100:
        raise ValueError("Kích thước trang (page_size) phải nằm trong khoảng từ 1 đến 100.")

    sort_by_clean = (sort_by or "created_at").strip().lower()
    if sort_by_clean not in ALLOWED_SORT_FIELDS:
        valid_sort_str = ", ".join(sorted(ALLOWED_SORT_FIELDS))
        raise ValueError(
            f"Trường sắp xếp '{sort_by}' không hợp lệ. Các trường được phép: {valid_sort_str}"
        )

    sort_order_clean = (sort_order or "desc").strip().lower()
    if sort_order_clean not in VALID_SORT_ORDERS:
        raise ValueError(
            f"Chiều sắp xếp '{sort_order}' không hợp lệ. Chỉ chấp nhận 'asc' hoặc 'desc'."
        )

    filters = [Task.project_id == project_id]

    if search is not None:
        search_clean = search.strip()
        if search_clean:
            filters.append(Task.title.ilike(f"%{search_clean}%"))

    if status is not None:
        status_clean = status.strip().upper()
        if status_clean not in VALID_TASK_STATUSES:
            valid_status_str = ", ".join(sorted(VALID_TASK_STATUSES))
            raise ValueError(
                f"Trạng thái '{status}' không hợp lệ. Các giá trị hợp lệ: {valid_status_str}"
            )
        filters.append(Task.status == status_clean)

    if priority is not None:
        priority_clean = priority.strip().upper()
        if priority_clean not in VALID_TASK_PRIORITIES:
            valid_priority_str = ", ".join(sorted(VALID_TASK_PRIORITIES))
            raise ValueError(
                f"Mức độ ưu tiên '{priority}' không hợp lệ. Các giá trị hợp lệ: {valid_priority_str}"
            )
        filters.append(Task.priority == priority_clean)

    if assignee_id is not None:
        filters.append(Task.assignee_id == assignee_id)

    count_query = select(func.count(Task.id)).where(*filters)
    total = db.scalar(count_query) or 0

    sort_column = getattr(Task, sort_by_clean)
    if sort_order_clean == "desc":
        order_clause = sort_column.desc()
        tie_breaker = Task.id.desc()
    else:
        order_clause = sort_column.asc()
        tie_breaker = Task.id.asc()

    offset = (page - 1) * page_size
    query = (
        select(Task)
        .options(joinedload(Task.assignee))
        .where(*filters)
        .order_by(order_clause, tie_breaker)
        .offset(offset)
        .limit(page_size)
    )

    tasks = list(db.scalars(query).unique().all())

    total_pages = math.ceil(total / page_size) if total > 0 else 0
    has_next = page < total_pages
    has_previous = page > 1 and total > 0

    return {
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages,
        "has_next": has_next,
        "has_previous": has_previous,
        "items": tasks,
    }


def create_project_task(
    db: Session,
    project_id: int,
    task_in: ProjectTaskCreate,
    current_user: User,
) -> Task:
    project = check_project_access(db, project_id, current_user)

    title_clean = task_in.title.strip()
    if not title_clean:
        raise ValueError("Tiêu đề công việc không được để trống.")

    status_clean = (task_in.status or "TODO").strip().upper()
    if status_clean not in VALID_TASK_STATUSES:
        valid_str = ", ".join(sorted(VALID_TASK_STATUSES))
        raise ValueError(f"Trạng thái '{task_in.status}' không hợp lệ. Các giá trị hợp lệ: {valid_str}")

    priority_clean = (task_in.priority or "MEDIUM").strip().upper()
    if priority_clean not in VALID_TASK_PRIORITIES:
        valid_str = ", ".join(sorted(VALID_TASK_PRIORITIES))
        raise ValueError(f"Mức độ ưu tiên '{task_in.priority}' không hợp lệ. Các giá trị hợp lệ: {valid_str}")

    due_date_utc = validate_and_normalize_due_date(task_in.due_date)
    validate_project_assignee(db, project, task_in.assignee_id)

    new_task = Task(
        title=title_clean,
        description=task_in.description.strip() if task_in.description else None,
        due_date=due_date_utc,
        status=status_clean,
        priority=priority_clean,
        project_id=project_id,
        assignee_id=task_in.assignee_id,
    )
    db.add(new_task)
    db.flush()
    log_activity(
        db,
        user_id=current_user.id,
        project_id=project_id,
        action=ACTION_TASK_CREATED,
        entity_type="task",
        entity_id=new_task.id,
        description=f"Tạo công việc '{title_clean}'.",
    )
    if task_in.assignee_id and task_in.assignee_id != current_user.id:
        create_notification(
            db,
            user_id=task_in.assignee_id,
            notif_type="TASK_ASSIGNED",
            title="Được giao công việc mới",
            message=f"Bạn vừa được giao công việc '{new_task.title}' trong dự án '{project.name}'.",
            project_id=project.id,
            task_id=new_task.id,
        )
    db.commit()
    db.refresh(new_task)

    created_task = db.scalar(
        select(Task)
        .options(joinedload(Task.assignee))
        .where(Task.id == new_task.id)
    )
    return created_task or new_task


def _normalize_optional_status(status: Optional[str]) -> Optional[str]:
    if status is None:
        return None
    status_clean = status.strip().upper()
    if status_clean not in VALID_TASK_STATUSES:
        valid_str = ", ".join(sorted(VALID_TASK_STATUSES))
        raise ValueError(f"Trạng thái '{status}' không hợp lệ. Các giá trị hợp lệ: {valid_str}")
    return status_clean


def _normalize_optional_priority(priority: Optional[str]) -> Optional[str]:
    if priority is None:
        return None
    priority_clean = priority.strip().upper()
    if priority_clean not in VALID_TASK_PRIORITIES:
        valid_str = ", ".join(sorted(VALID_TASK_PRIORITIES))
        raise ValueError(f"Mức độ ưu tiên '{priority}' không hợp lệ. Các giá trị hợp lệ: {valid_str}")
    return priority_clean


def can_delete_project_task(db: Session, project: Project, user: User) -> bool:
    if user.role and user.role.strip().upper() == "ADMIN":
        return True
    if project.owner_id == user.id:
        return True

    member = db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project.id,
            ProjectMember.user_id == user.id,
        )
    )
    if not member or not member.role:
        return False

    return member.role.strip().upper() in {"OWNER", "MANAGER"}


def update_task(
    db: Session,
    task_id: int,
    task_in: TaskUpdate,
    current_user: User,
) -> Task:
    task = db.scalar(select(Task).where(Task.id == task_id))
    if not task:
        raise NotFoundError(f"Không tìm thấy công việc với ID {task_id}.")

    project = check_project_access(db, task.project_id, current_user)

    is_manager_or_owner = can_delete_project_task(db, project, current_user)
    is_assignee = task.assignee_id == current_user.id
    is_unassigned = task.assignee_id is None

    if not is_manager_or_owner and not is_assignee and not is_unassigned:
        raise PermissionDeniedError(
            "Chỉ chủ dự án, quản lý hoặc người được giao việc (assignee) mới có quyền cập nhật công việc này."
        )

    old_status = task.status
    old_assignee_id = task.assignee_id
    update_data = task_in.model_dump(exclude_unset=True)

    if not is_manager_or_owner and not is_unassigned:
        restricted_fields = {"title", "priority", "due_date", "assignee_id"}
        forbidden_sent = restricted_fields.intersection(update_data.keys())
        if forbidden_sent:
            raise PermissionDeniedError(
                "Người được giao việc (assignee) chỉ được cập nhật trạng thái hoặc mô tả công việc."
            )

    if "title" in update_data:
        raw_title = update_data["title"]
        if raw_title is None or not raw_title.strip():
            raise ValueError("Tiêu đề công việc không được để trống.")
        task.title = raw_title.strip()

    if "description" in update_data:
        raw_desc = update_data["description"]
        task.description = raw_desc.strip() if raw_desc is not None else None

    if "due_date" in update_data:
        task.due_date = validate_and_normalize_due_date(update_data["due_date"])

    if "status" in update_data:
        raw_status = update_data["status"]
        if raw_status is None or not raw_status.strip():
            raise ValueError("Trạng thái công việc không được để trống.")
        status_clean = raw_status.strip().upper()
        validate_status_transition(task.status, status_clean)
        task.status = status_clean

    if "priority" in update_data:
        raw_priority = update_data["priority"]
        if raw_priority is None or not raw_priority.strip():
            raise ValueError("Mức độ ưu tiên không được để trống.")
        task.priority = _normalize_optional_priority(raw_priority)

    if "assignee_id" in update_data:
        new_assignee_id = update_data["assignee_id"]
        validate_project_assignee(db, project, new_assignee_id)
        task.assignee_id = new_assignee_id
        if (
            new_assignee_id is not None
            and new_assignee_id != old_assignee_id
            and new_assignee_id != current_user.id
        ):
            create_notification(
                db,
                user_id=new_assignee_id,
                notif_type="TASK_ASSIGNED",
                title="Được giao công việc mới",
                message=f"Bạn vừa được giao công việc '{task.title}' trong dự án '{project.name}'.",
                project_id=project.id,
                task_id=task.id,
            )

    if "status" in update_data and task.status != old_status:
        recipients: set[int] = set()
        if task.assignee_id and task.assignee_id != current_user.id:
            recipients.add(task.assignee_id)
        if project.owner_id and project.owner_id != current_user.id:
            recipients.add(project.owner_id)
        for recipient_id in recipients:
            create_notification(
                db,
                user_id=recipient_id,
                notif_type="TASK_STATUS_CHANGED",
                title="Trạng thái công việc thay đổi",
                message=f"Công việc '{task.title}' đã chuyển trạng thái từ {old_status} sang {task.status}.",
                project_id=project.id,
                task_id=task.id,
            )

    status_changed = "status" in update_data and old_status != task.status
    if status_changed:
        log_activity(
            db,
            user_id=current_user.id,
            project_id=task.project_id,
            action=ACTION_TASK_STATUS_CHANGED,
            entity_type="task",
            entity_id=task.id,
            description=f"Đổi trạng thái công việc '{task.title}' từ {old_status} sang {task.status}.",
        )
    else:
        log_activity(
            db,
            user_id=current_user.id,
            project_id=task.project_id,
            action=ACTION_TASK_UPDATED,
            entity_type="task",
            entity_id=task.id,
            description=f"Cập nhật công việc '{task.title}'.",
        )

    db.commit()
    return get_task_for_user(db, task.id, current_user)


def change_task_status(
    db: Session,
    task_id: int,
    status: str,
    current_user: User,
) -> Task:
    task = get_task_for_user(db, task_id, current_user)
    project = check_project_access(db, task.project_id, current_user)
    is_manager_or_owner = can_delete_project_task(db, project, current_user)
    is_assignee = task.assignee_id == current_user.id
    is_unassigned = task.assignee_id is None
    if not is_manager_or_owner and not is_assignee and not is_unassigned:
        raise PermissionDeniedError(
            "Chỉ chủ dự án, quản lý hoặc người được giao việc (assignee) mới có quyền cập nhật trạng thái công việc này."
        )

    new_status = _normalize_optional_status(status)
    if new_status is None:
        raise ValueError("Trạng thái công việc không được để trống.")
    validate_status_transition(task.status, new_status)
    old_status = task.status
    task.status = new_status
    log_activity(
        db,
        user_id=current_user.id,
        project_id=task.project_id,
        action=ACTION_TASK_STATUS_CHANGED,
        entity_type="task",
        entity_id=task.id,
        description=f"Đổi trạng thái công việc '{task.title}' từ {old_status} sang {new_status}.",
    )
    db.commit()
    return get_task_for_user(db, task.id, current_user)


def delete_task(db: Session, task_id: int, current_user: User) -> None:
    from app.models.attachment import Attachment
    from app.services.attachment import delete_physical_file

    task = db.scalar(select(Task).where(Task.id == task_id))
    if not task:
        raise NotFoundError(f"Không tìm thấy công việc với ID {task_id}.")

    project = db.scalar(
        select(Project).where(
            Project.id == task.project_id,
            Project.is_deleted.is_(False),
        )
    )
    if not project:
        raise NotFoundError(f"Không tìm thấy dự án với ID {task.project_id}.")

    if not can_delete_project_task(db, project, current_user):
        raise PermissionDeniedError("Bạn không có quyền xóa công việc này.")

    stored_paths = list(
        db.scalars(select(Attachment.stored_path).where(Attachment.task_id == task.id)).all()
    )
    title = task.title
    project_id = task.project_id
    log_activity(
        db,
        user_id=current_user.id,
        project_id=project_id,
        action=ACTION_TASK_DELETED,
        entity_type="task",
        entity_id=task.id,
        description=f"Xóa công việc '{title}'.",
    )
    db.delete(task)
    db.commit()
    for stored_path in stored_paths:
        delete_physical_file(stored_path)