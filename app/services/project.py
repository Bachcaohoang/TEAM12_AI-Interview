"""Nghiệp vụ quản lý dự án."""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.models.project import Project, ProjectMember
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.schemas.project_member import ProjectMemberAdd


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

    query = query.order_by(Project.id.desc()).offset(skip).limit(limit)
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
    """Cập nhật dự án (chỉ OWNER)."""
    if project.owner_id != current_user.id:
        raise PermissionDeniedError("Chỉ OWNER mới có quyền sửa dự án này.")

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
    """Xóa dự án (chỉ OWNER)."""
    if project.owner_id != current_user.id:
        raise PermissionDeniedError("Chỉ OWNER mới có quyền xóa dự án này.")

    db.delete(project)
    db.commit()


def add_project_member(
    db: Session,
    project: Project,
    member_in: ProjectMemberAdd,
) -> ProjectMember:
    """Thêm thành viên vào dự án, không cho thêm trùng."""
    target_user = db.scalar(select(User).where(User.id == member_in.user_id))
    if not target_user:
        raise NotFoundError(f"Không tìm thấy người dùng với ID {member_in.user_id}.")

    if target_user.id == project.owner_id:
        raise ValueError("Người dùng này đã là chủ sở hữu (OWNER) của dự án.")

    existing_member = db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project.id,
            ProjectMember.user_id == member_in.user_id,
        )
    )
    if existing_member:
        raise ValueError("Người dùng này đã là thành viên của dự án.")

    new_member = ProjectMember(
        project_id=project.id,
        user_id=member_in.user_id,
        role=(member_in.role or "MEMBER").strip().upper(),
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
    if user_id == project.owner_id:
        raise ValueError("Không thể xóa chủ sở hữu (OWNER) khỏi dự án.")

    member = db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project.id,
            ProjectMember.user_id == user_id,
        )
    )
    if not member:
        raise NotFoundError(f"Không tìm thấy thành viên với user_id {user_id} trong dự án.")

    if (member.role or "").strip().upper() == "OWNER":
        raise ValueError("Không thể xóa chủ sở hữu (OWNER) khỏi dự án.")

    db.delete(member)
    db.commit()