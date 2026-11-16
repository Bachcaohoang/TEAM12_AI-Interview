"""Nghiệp vụ liên quan đến Dự án (Project)."""

from sqlalchemy.orm import Session

from app.core.exceptions import (
    NotProjectMemberException,
    ProjectNotFoundException,
)
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.user import User


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
