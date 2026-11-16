"""Nghiệp vụ liên quan đến Dự án (Project)."""

from sqlalchemy.orm import Session

from app.core.exceptions import (
    NotProjectMemberException,
    ProjectNotFoundException,
)
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.user import User
from app.schemas.project import ProjectCreate


def create_project(db: Session, project_in: ProjectCreate, current_user: User) -> Project:
    """Tạo mới dự án và tự động gán người tạo làm OWNER.

    Quy trình:
    1. Tạo bản ghi Project với owner_id là ID của current_user.
    2. Tự động thêm current_user vào bảng project_members với role='OWNER'.
    3. Commit transaction và trả về đối tượng Project đã tạo.
    """
    project = Project(
        name=project_in.name,
        description=project_in.description,
        owner_id=current_user.id,
    )
    db.add(project)
    db.flush()

    project_member = ProjectMember(
        project_id=project.id,
        user_id=current_user.id,
        role="OWNER",
    )
    db.add(project_member)
    db.commit()
    db.refresh(project)

    return project


def get_project_detail(db: Session, project_id: int, current_user: User) -> Project:
    """Lấy thông tin chi tiết của dự án nếu người dùng là thành viên.

    Quy tắc phân quyền:
    - Dự án không tồn tại -> 404 ProjectNotFoundException.
    - Người dùng không phải là owner và cũng không nằm trong project_members -> 403 NotProjectMemberException.
    - Chỉ thành viên dự án mới được xem thông tin chi tiết -> 200 OK trả về Project.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise ProjectNotFoundException()

    # Kiểm tra người dùng có phải là thành viên dự án không (Owner hoặc có trong ProjectMember)
    is_owner = project.owner_id == current_user.id
    is_member = (
        is_owner
        or db.query(ProjectMember)
        .filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == current_user.id,
        )
        .first()
        is not None
    )

    if not is_member:
        raise NotProjectMemberException()

    return project
