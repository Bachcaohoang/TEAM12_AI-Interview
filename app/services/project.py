"""Nghiệp vụ quản lý dự án."""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.task import Task
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectMemberAdd, ProjectUpdate


def get_projects(
    db: Session,
    current_user: User,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    status: Optional[str] = None,
) -> list[Project]:
    """
    Lấy danh sách dự án:
    - Nếu admin hoặc manager: xem được tất cả các dự án trong hệ thống.
    - Nếu user thông thường: xem các dự án do chính mình tạo/sở hữu.
    Hỗ trợ tìm kiếm theo tên và lọc theo trạng thái.
    """
    query = select(Project)
    if current_user.role not in ("admin", "manager"):
        query = query.where(Project.owner_id == current_user.id)

    if search:
        query = query.where(Project.name.ilike(f"%{search.strip()}%"))
    if status:
        query = query.where(Project.status == status.strip())

    query = query.offset(skip).limit(limit).order_by(Project.id.desc())
    return list(db.scalars(query).all())


def get_project_by_id(db: Session, project_id: int) -> Optional[Project]:
    """Tìm dự án theo ID."""
    return db.scalar(select(Project).where(Project.id == project_id))


def create_project(db: Session, project_in: ProjectCreate, owner_id: int) -> Project:
    """Tạo dự án mới."""
    project = Project(
        name=project_in.name.strip(),
        description=project_in.description.strip() if project_in.description else None,
        status=project_in.status or "in_progress",
        owner_id=owner_id,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def update_project(
    db: Session, project: Project, project_in: ProjectUpdate, current_user: User
) -> Project:
    """Cập nhật dự án (yêu cầu là chủ dự án hoặc admin)."""
    if current_user.role != "admin" and project.owner_id != current_user.id:
        raise PermissionDeniedError("Bạn không có quyền sửa dự án này.")

    if project_in.name is not None:
        project.name = project_in.name.strip()
    if project_in.description is not None:
        project.description = project_in.description.strip()
    if project_in.status is not None:
        project.status = project_in.status.strip()

    db.commit()
    db.refresh(project)
    return project


def delete_project(db: Session, project: Project, current_user: User) -> None:
    """Xóa mềm dự án (giữ lại dữ liệu trong DB, cập nhật is_deleted và deleted_at)."""
    if current_user.role != "admin" and project.owner_id != current_user.id:
        raise PermissionDeniedError("Bạn không có quyền xóa dự án này.")

    project.is_deleted = True
    project.deleted_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(project)

    
def get_project_members(
    db: Session,
    project_id: int,
    current_user: User,
) -> list[dict]:
    """Lấy danh sách thành viên và role trong dự án."""
    project = get_project_by_id(db, project_id)
    if not project:
        raise NotFoundError("Project không tồn tại.")

    membership = db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == current_user.id,
        )
    )
    is_owner = project.owner_id == current_user.id
    is_admin = current_user.role == "admin"

    if not membership and not is_owner and not is_admin:
        raise PermissionDeniedError("Bạn không có quyền xem danh sách thành viên của project này.")

    rows = db.execute(
        select(ProjectMember, User)
        .join(User, ProjectMember.user_id == User.id)
        .where(ProjectMember.project_id == project_id)
    ).all()

    members: list[dict] = []
    seen_user_ids: set[int] = set()

    for member, user in rows:
        seen_user_ids.add(member.user_id)
        members.append(
            {
                "user_id": member.user_id,
                "role": member.role,
                "email": getattr(user, "email", None),
                "full_name": getattr(user, "full_name", None),
                "joined_at": getattr(member, "joined_at", getattr(member, "created_at", None)),
            }
        )

    # Đảm bảo chủ sở hữu dự án luôn có mặt trong danh sách trả về
    if project.owner_id and project.owner_id not in seen_user_ids:
        owner = db.scalar(select(User).where(User.id == project.owner_id))
        if owner:
            members.insert(
                0,
                {
                    "user_id": owner.id,
                    "role": "OWNER",
                    "email": getattr(owner, "email", None),
                    "full_name": getattr(owner, "full_name", None),
                    "joined_at": getattr(project, "created_at", None),
                },
            )

    return members


def add_project_member(
    db: Session,
    project: Project,
    member_in: ProjectMemberAdd,
) -> ProjectMember:
    """Thêm thành viên vào dự án (chỉ OWNER, kiểm tra user tồn tại và chống trùng)."""
    user = db.scalar(select(User).where(User.id == member_in.user_id))
    if not user:
        raise NotFoundError("Không tìm thấy người dùng.")

    if user.id == project.owner_id:
        raise ValueError("Người dùng này đã là chủ sở hữu (OWNER) của dự án.")

    existing = db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project.id,
            ProjectMember.user_id == member_in.user_id,
        )
    )
    if existing:
        raise ValueError("Người dùng đã là thành viên của dự án.")

    role_clean = (member_in.role or "MEMBER").strip().upper()
    if role_clean not in ("OWNER", "MANAGER", "MEMBER"):
        raise ValueError("Role không hợp lệ (chỉ chấp nhận OWNER, MANAGER, MEMBER).")

    new_member = ProjectMember(
        project_id=project.id,
        user_id=member_in.user_id,
        role=role_clean,
    )
    db.add(new_member)
    db.commit()
    db.refresh(new_member)
    return new_member


def remove_project_member(
    db: Session,
    project: Project,
    user_id: int,
) -> None:
    """Xóa thành viên khỏi dự án (chỉ OWNER, không được xóa OWNER)."""
    if user_id == project.owner_id:
        raise ValueError("Không thể xóa chủ sở hữu (OWNER) khỏi dự án.")

    member = db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project.id,
            ProjectMember.user_id == user_id,
        )
    )
    if not member:
        raise NotFoundError("Thành viên không tồn tại trong dự án.")

    db.delete(member)
    db.commit()


def get_projects(
    db: Session,
    current_user: User,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    status: Optional[str] = None,
) -> list[Project]:
    """
    Lấy danh sách dự án chưa bị xóa mềm:
    - Nếu admin hoặc manager: xem được tất cả các dự án trong hệ thống.
    - Nếu user thông thường: xem các dự án do chính mình tạo/sở hữu.
    """
    query = select(Project).where(Project.is_deleted.is_(False))
    if current_user.role not in ("admin", "manager"):
        query = query.where(Project.owner_id == current_user.id)

    if search:
        query = query.where(Project.name.ilike(f"%{search.strip()}%"))
    if status:
        query = query.where(Project.status == status.strip())

    query = query.offset(skip).limit(limit).order_by(Project.id.desc())
    return list(db.scalars(query).all())


def get_project_by_id(db: Session, project_id: int) -> Optional[Project]:
    """Tìm dự án theo ID (bỏ qua dự án đã xóa mềm)."""
    return db.scalar(
        select(Project).where(
            Project.id == project_id,
            Project.is_deleted.is_(False),
        )
    )

def get_project_dashboard(
    db: Session,
    project_id: int,
    current_user: User,
) -> dict:
    """Thống kê tỷ lệ hoàn thành task, số lượng task theo trạng thái và theo assignee của dự án."""
    project = get_project_by_id(db, project_id)
    if not project:
        raise NotFoundError("Project không tồn tại.")

    membership = db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == current_user.id,
        )
    )
    is_owner = project.owner_id == current_user.id
    is_admin = (current_user.role or "").strip().upper() == "ADMIN"

    if not membership and not is_owner and not is_admin:
        raise PermissionDeniedError("Bạn không có quyền xem dashboard của dự án này.")

    tasks = list(db.scalars(select(Task).where(Task.project_id == project_id)).all())
    total_tasks = len(tasks)

    status_counts = {"TODO": 0, "IN_PROGRESS": 0, "DONE": 0}
    assignee_buckets: dict[Optional[int], dict] = {}

    # Lấy thông tin user cho các assignee_id xuất hiện trong danh sách task
    assignee_ids = {t.assignee_id for t in tasks if t.assignee_id is not None}
    users_map: dict[int, User] = {}
    if assignee_ids:
        users = list(db.scalars(select(User).where(User.id.in_(assignee_ids))).all())
        users_map = {u.id: u for u in users}

    for task in tasks:
        st = (task.status or "TODO").strip().upper()
        if st in status_counts:
            status_counts[st] += 1

        aid = task.assignee_id
        if aid not in assignee_buckets:
            user_obj = users_map.get(aid) if aid is not None else None
            assignee_buckets[aid] = {
                "assignee_id": aid,
                "full_name": user_obj.full_name if user_obj else "Chưa phân công",
                "email": user_obj.email if user_obj else None,
                "total_tasks": 0,
                "todo": 0,
                "in_progress": 0,
                "done": 0,
            }

        bucket = assignee_buckets[aid]
        bucket["total_tasks"] += 1
        if st == "TODO":
            bucket["todo"] += 1
        elif st == "IN_PROGRESS":
            bucket["in_progress"] += 1
        elif st == "DONE":
            bucket["done"] += 1

    completed_tasks = status_counts["DONE"]
    completion_rate = round((completed_tasks / total_tasks) * 100, 2) if total_tasks > 0 else 0.0

    tasks_by_assignee: list[dict] = []
    for bucket in assignee_buckets.values():
        b_total = bucket["total_tasks"]
        b_rate = round((bucket["done"] / b_total) * 100, 2) if b_total > 0 else 0.0
        tasks_by_assignee.append({**bucket, "completion_rate": b_rate})

    # Sắp xếp assignee có nhiều task nhất lên đầu, nhóm "Chưa phân công" xuống cuối
    tasks_by_assignee.sort(key=lambda x: (x["assignee_id"] is None, -x["total_tasks"]))

    return {
        "project_id": project.id,
        "project_name": project.name,
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "completion_rate": completion_rate,
        "tasks_by_status": status_counts,
        "tasks_by_assignee": tasks_by_assignee,
    }