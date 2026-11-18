"""Nghiệp vụ quản lý công việc (Task)."""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.task import Task
from app.models.user import User

# Các giá trị hợp lệ theo nghiệp vụ và model
VALID_TASK_STATUSES = {"TODO", "IN_PROGRESS", "DONE"}
VALID_TASK_PRIORITIES = {"LOW", "MEDIUM", "HIGH"}


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
) -> list[Task]:
    """
    Lấy danh sách công việc trong một dự án có hỗ trợ tìm kiếm và lọc:
    - Bắt buộc kiểm tra quyền truy cập dự án của user hiện tại.
    - Chỉ lấy công việc thuộc đúng project_id (không lẫn sang dự án khác).
    - search: tìm kiếm theo title (không phân biệt hoa thường, chứa từ khóa).
    - status: lọc theo trạng thái (TODO, IN_PROGRESS, DONE).
    - priority: lọc theo mức độ ưu tiên (LOW, MEDIUM, HIGH).
    - assignee_id: lọc theo ID người được giao việc.
    - Kết hợp tất cả điều kiện bằng logic AND tại database query.
    """
    # 1. Kiểm tra quyền truy cập dự án
    check_project_access(db, project_id, current_user)

    # 2. Xây dựng truy vấn cơ sở dữ liệu
    query = (
        select(Task)
        .options(joinedload(Task.assignee))
        .where(Task.project_id == project_id)
    )

    # 3. Lọc theo search (tiêu đề công việc)
    if search is not None:
        search_clean = search.strip()
        if search_clean:
            query = query.where(Task.title.ilike(f"%{search_clean}%"))

    # 4. Lọc theo status (trạng thái)
    if status is not None:
        status_clean = status.strip().upper()
        if status_clean not in VALID_TASK_STATUSES:
            valid_str = ", ".join(sorted(VALID_TASK_STATUSES))
            raise ValueError(
                f"Trạng thái '{status}' không hợp lệ. Các giá trị hợp lệ: {valid_str}"
            )
        query = query.where(Task.status == status_clean)

    # 5. Lọc theo priority (mức độ ưu tiên)
    if priority is not None:
        priority_clean = priority.strip().upper()
        if priority_clean not in VALID_TASK_PRIORITIES:
            valid_str = ", ".join(sorted(VALID_TASK_PRIORITIES))
            raise ValueError(
                f"Mức độ ưu tiên '{priority}' không hợp lệ. Các giá trị hợp lệ: {valid_str}"
            )
        query = query.where(Task.priority == priority_clean)

    # 6. Lọc theo assignee_id (người được giao)
    if assignee_id is not None:
        query = query.where(Task.assignee_id == assignee_id)

    # Thực thi truy vấn với toàn bộ điều kiện AND
    tasks = list(db.scalars(query).unique().all())
    return tasks
