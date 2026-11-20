"""Nghiệp vụ quản lý dự án."""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectUpdate


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
    """Xóa dự án (yêu cầu là chủ dự án hoặc admin)."""
    if current_user.role != "admin" and project.owner_id != current_user.id:
        raise PermissionDeniedError("Bạn không có quyền xóa dự án này.")

    db.delete(project)
    db.commit()


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