"""Nghiệp vụ quản lý công việc (Task)."""

import math
from typing import Any, Optional
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.task import Task
from app.models.user import User
from app.schemas.task import ProjectTaskCreate

# Các giá trị hợp lệ theo nghiệp vụ và model
VALID_TASK_STATUSES = {"TODO", "IN_PROGRESS", "DONE"}
VALID_TASK_PRIORITIES = {"LOW", "MEDIUM", "HIGH"}
ALLOWED_SORT_FIELDS = {"created_at", "updated_at", "title", "status", "priority"}
VALID_SORT_ORDERS = {"asc", "desc"}


def is_user_project_member(db: Session, project: Project, user: User) -> bool:
    """
    Kiểm tra xem user có quyền truy cập vào project hay không:
    - Admin hệ thống có toàn quyền.
    - Chủ sở hữu dự án (Owner) có toàn quyền.
    - Thành viên dự án trong bảng project_members.
    """
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
    """
    Kiểm tra sự tồn tại của dự án và quyền truy cập của người dùng hiện tại.
    - Raise NotFoundError nếu dự án không tồn tại.
    - Raise PermissionDeniedError nếu người dùng không phải thành viên dự án.
    """
    project = db.scalar(select(Project).where(Project.id == project_id))
    if not project:
        raise NotFoundError(f"Không tìm thấy dự án với ID {project_id}.")

    if not is_user_project_member(db, project, current_user):
        raise PermissionDeniedError("Bạn không có quyền truy cập vào dự án này.")

    return project


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
    """
    Lấy danh sách công việc trong một dự án có hỗ trợ Search, Filter, Sort và Pagination.
    """
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


def get_task_by_id(db: Session, task_id: int, current_user: User) -> Task:
    """
    Lấy chi tiết một công việc theo ID:
    - Raise NotFoundError (404) nếu công việc không tồn tại.
    - Kiểm tra user hiện tại thuộc project của công việc (PermissionDeniedError -> 403).
    """
    task = db.scalar(
        select(Task)
        .options(joinedload(Task.assignee))
        .where(Task.id == task_id)
    )
    if not task:
        raise NotFoundError(f"Không tìm thấy công việc với ID {task_id}.")

    check_project_access(db, task.project_id, current_user)
    return task


def create_project_task(
    db: Session,
    project_id: int,
    task_in: ProjectTaskCreate,
    current_user: User,
) -> Task:
    """
    Tạo công việc mới trong một dự án:
    - Kiểm tra dự án tồn tại (NotFoundError -> 404).
    - Kiểm tra user hiện tại là thành viên dự án, chủ dự án hoặc Admin (PermissionDeniedError -> 403).
    - Chuẩn hóa và kiểm tra hợp lệ title, status, priority, assignee_id.
    """
    check_project_access(db, project_id, current_user)

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

    if task_in.assignee_id is not None:
        assignee = db.scalar(select(User).where(User.id == task_in.assignee_id))
        if not assignee:
            raise NotFoundError(f"Không tìm thấy người dùng được giao việc với ID {task_in.assignee_id}.")

    new_task = Task(
        title=title_clean,
        description=task_in.description.strip() if task_in.description else None,
        due_date=task_in.due_date,
        status=status_clean,
        priority=priority_clean,
        project_id=project_id,
        assignee_id=task_in.assignee_id,
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    created_task = db.scalar(
        select(Task)
        .options(joinedload(Task.assignee))
        .where(Task.id == new_task.id)
    )
    return created_task or new_task