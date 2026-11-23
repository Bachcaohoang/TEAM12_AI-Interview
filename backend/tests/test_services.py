"""Bộ test tự động cho tầng Service chính: Auth, Project, Task."""

import pytest
from datetime import datetime, timedelta, timezone

from app.core.exceptions import AuthenticationError, DuplicateError, NotFoundError, PermissionDeniedError
from app.core.security import hash_password
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.task import Task
from app.models.user import User
from app.schemas.auth import TokenResponse
from app.schemas.project import ProjectCreate, ProjectMemberAdd, ProjectUpdate
from app.schemas.task import ProjectTaskCreate, TaskUpdate
from app.schemas.user import PasswordChangeRequest, UserCreate
from app.services import auth as auth_service
from app.services import project as project_service
from app.services import task as task_service
from app.services import user as user_service


# ==============================================================================
# 1. TEST SUITE CHO AUTH & USER SERVICE
# ==============================================================================

class TestAuthService:
    def test_authenticate_user_success(self, db_session):
        user_in = UserCreate(
            email="auth_svc@test.com",
            password="Password123",
            full_name="Auth Service Test",
            role="USER",
        )
        created = user_service.create_user(db_session, user_in)
        assert created.id is not None

        authenticated = auth_service.authenticate_user(
            db_session, email="auth_svc@test.com", password="Password123"
        )
        assert authenticated is not None
        assert authenticated.id == created.id

    def test_authenticate_user_wrong_password_or_email(self, db_session):
        user_in = UserCreate(
            email="wrong_pwd@test.com",
            password="Password123",
            full_name="Wrong Pwd Test",
        )
        user_service.create_user(db_session, user_in)

        # Sai mật khẩu
        assert auth_service.authenticate_user(db_session, "wrong_pwd@test.com", "WrongPassword") is None
        # Sai email
        assert auth_service.authenticate_user(db_session, "nonexistent@test.com", "Password123") is None

    def test_create_and_refresh_tokens(self, db_session):
        user = User(
            email="token_svc@test.com",
            full_name="Token User",
            hashed_password=hash_password("Password123"),
            role="USER",
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        tokens = auth_service.create_user_tokens(user)
        assert isinstance(tokens, TokenResponse)
        assert tokens.access_token is not None
        assert tokens.refresh_token is not None

        # Refresh token hợp lệ
        refreshed = auth_service.refresh_user_tokens(db_session, tokens.refresh_token)
        assert refreshed.access_token is not None
        assert refreshed.refresh_token is not None

    def test_refresh_token_invalid_or_inactive_user(self, db_session):
        with pytest.raises(AuthenticationError):
            auth_service.refresh_user_tokens(db_session, "invalid.jwt.token")

        inactive_user = User(
            email="inactive@test.com",
            full_name="Inactive User",
            hashed_password=hash_password("Password123"),
            role="USER",
            is_active=False,
        )
        db_session.add(inactive_user)
        db_session.commit()
        db_session.refresh(inactive_user)

        tokens = auth_service.create_user_tokens(inactive_user)
        with pytest.raises(AuthenticationError, match="đã bị vô hiệu hóa"):
            auth_service.refresh_user_tokens(db_session, tokens.refresh_token)

    def test_request_password_reset(self, db_session):
        user = User(
            email="reset_svc@test.com",
            full_name="Reset User",
            hashed_password=hash_password("Password123"),
            role="USER",
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        reset_token = auth_service.request_password_reset(db_session, "reset_svc@test.com")
        assert reset_token is not None

        with pytest.raises(NotFoundError):
            auth_service.request_password_reset(db_session, "notfound@test.com")


# ==============================================================================
# 2. TEST SUITE CHO PROJECT SERVICE
# ==============================================================================

class TestProjectService:
    @pytest.fixture
    def project_environment(self, db_session):
        owner = User(
            email="p_owner@test.com",
            full_name="Project Owner",
            hashed_password=hash_password("Password123"),
            role="USER",
            is_active=True,
        )
        member = User(
            email="p_member@test.com",
            full_name="Project Member",
            hashed_password=hash_password("Password123"),
            role="USER",
            is_active=True,
        )
        outsider = User(
            email="p_outsider@test.com",
            full_name="Project Outsider",
            hashed_password=hash_password("Password123"),
            role="USER",
            is_active=True,
        )
        admin = User(
            email="p_admin@test.com",
            full_name="Admin User",
            hashed_password=hash_password("Password123"),
            role="ADMIN",
            is_active=True,
        )
        db_session.add_all([owner, member, outsider, admin])
        db_session.commit()
        for u in (owner, member, outsider, admin):
            db_session.refresh(u)

        return {
            "owner": owner,
            "member": member,
            "outsider": outsider,
            "admin": admin,
        }

    def test_create_and_get_project(self, db_session, project_environment):
        owner = project_environment["owner"]
        proj_in = ProjectCreate(
            name="Dự án Service Unit Test",
            description="Mô tả dự án",
            status="in_progress",
        )
        project = project_service.create_project(db_session, proj_in, owner.id)
        assert project.id is not None
        assert project.owner_id == owner.id
        assert project.name == "Dự án Service Unit Test"

        found = project_service.get_project_by_id(db_session, project.id)
        assert found is not None
        assert found.id == project.id

    def test_update_and_soft_delete_project(self, db_session, project_environment):
        owner = project_environment["owner"]
        outsider = project_environment["outsider"]
        admin = project_environment["admin"]

        project = project_service.create_project(
            db_session, ProjectCreate(name="Dự án Cần Sửa", description="Gốc"), owner.id
        )

        # Người ngoài không được sửa
        with pytest.raises(PermissionDeniedError):
            project_service.update_project(
                db_session, project, ProjectUpdate(name="Đổi tên"), outsider
            )

        # Chủ sở hữu sửa thành công
        updated = project_service.update_project(
            db_session, project, ProjectUpdate(name="Tên Mới", description="Mô tả mới"), owner
        )
        assert updated.name == "Tên Mới"

        # Người ngoài không được xóa
        with pytest.raises(PermissionDeniedError):
            project_service.delete_project(db_session, project, outsider)

        # Xóa mềm thành công
        project_service.delete_project(db_session, project, owner)
        assert project.is_deleted is True
        assert project_service.get_project_by_id(db_session, project.id) is None

    def test_add_and_remove_project_member(self, db_session, project_environment):
        owner = project_environment["owner"]
        member = project_environment["member"]

        project = project_service.create_project(
            db_session, ProjectCreate(name="Dự án Thành Viên"), owner.id
        )

        # Thêm thành viên
        add_in = ProjectMemberAdd(user_id=member.id, role="MEMBER")
        new_pm = project_service.add_project_member(db_session, project, add_in)
        assert new_pm.user_id == member.id
        assert new_pm.role == "MEMBER"

        # Không được thêm trùng
        with pytest.raises(ValueError, match="đã là thành viên"):
            project_service.add_project_member(db_session, project, add_in)

        # Không được thêm chính OWNER làm member
        with pytest.raises(ValueError, match="đã là chủ sở hữu"):
            project_service.add_project_member(
                db_session, project, ProjectMemberAdd(user_id=owner.id, role="MEMBER")
            )

        # Danh sách thành viên
        members = project_service.get_project_members(db_session, project.id, owner)
        assert len(members) == 2  # OWNER + MEMBER

        # Xóa thành viên
        project_service.remove_project_member(db_session, project, member.id)
        members_after = project_service.get_project_members(db_session, project.id, owner)
        assert len(members_after) == 1

        # Không được xóa OWNER
        with pytest.raises(ValueError, match="Không thể xóa chủ sở hữu"):
            project_service.remove_project_member(db_session, project, owner.id)


# ==============================================================================
# 3. TEST SUITE CHO TASK SERVICE
# ==============================================================================

class TestTaskService:
    @pytest.fixture
    def task_environment(self, db_session):
        owner = User(
            email="t_owner@test.com",
            full_name="Task Owner",
            hashed_password=hash_password("Password123"),
            role="USER",
            is_active=True,
        )
        assignee = User(
            email="t_assignee@test.com",
            full_name="Task Assignee",
            hashed_password=hash_password("Password123"),
            role="USER",
            is_active=True,
        )
        outsider = User(
            email="t_outsider@test.com",
            full_name="Task Outsider",
            hashed_password=hash_password("Password123"),
            role="USER",
            is_active=True,
        )
        db_session.add_all([owner, assignee, outsider])
        db_session.commit()
        for u in (owner, assignee, outsider):
            db_session.refresh(u)

        project = Project(name="Dự án Task Svc", owner_id=owner.id)
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        db_session.add(ProjectMember(project_id=project.id, user_id=assignee.id, role="MEMBER"))
        db_session.commit()

        return {
            "owner": owner,
            "assignee": assignee,
            "outsider": outsider,
            "project": project,
        }

    def test_create_and_get_task_service(self, db_session, task_environment):
        owner = task_environment["owner"]
        assignee = task_environment["assignee"]
        outsider = task_environment["outsider"]
        project = task_environment["project"]

        future_date = datetime.now(timezone.utc) + timedelta(days=5)
        task_in = ProjectTaskCreate(
            title="Task Service Mẫu",
            description="Mô tả chi tiết",
            priority="HIGH",
            status="TODO",
            due_date=future_date,
            assignee_id=assignee.id,
        )

        task = task_service.create_project_task(db_session, project.id, task_in, owner)
        assert task.id is not None
        assert task.title == "Task Service Mẫu"
        assert task.assignee_id == assignee.id

        # Thành viên lấy được task
        fetched = task_service.get_task_for_user(db_session, task.id, assignee)
        assert fetched.id == task.id

        # Người ngoài lấy task bị 403
        with pytest.raises(PermissionDeniedError):
            task_service.get_task_for_user(db_session, task.id, outsider)

    def test_task_workflow_and_validation(self, db_session, task_environment):
        owner = task_environment["owner"]
        project = task_environment["project"]

        # Không tạo được task có hạn chót quá khứ
        past_date = datetime.now(timezone.utc) - timedelta(days=2)
        with pytest.raises(ValueError, match="không được nằm trong quá khứ"):
            task_service.create_project_task(
                db_session,
                project.id,
                ProjectTaskCreate(title="Task Quá Hạn", due_date=past_date),
                owner,
            )

        task = task_service.create_project_task(
            db_session,
            project.id,
            ProjectTaskCreate(title="Task Workflow"),
            owner,
        )
        assert task.status == "TODO"

        # Chuyển trạng thái TODO -> IN_PROGRESS: Hợp lệ
        updated_task = task_service.change_task_status(db_session, task.id, "IN_PROGRESS", owner)
        assert updated_task.status == "IN_PROGRESS"

        # Chuyển trực tiếp từ TODO -> DONE: Vi phạm workflow (TODO chỉ có thể sang IN_PROGRESS)
        task_todo = task_service.create_project_task(
            db_session,
            project.id,
            ProjectTaskCreate(title="Task TODO"),
            owner,
        )
        with pytest.raises(ValueError, match="Không thể chuyển trạng thái"):
            task_service.change_task_status(db_session, task_todo.id, "DONE", owner)

    def test_delete_task_service(self, db_session, task_environment):
        owner = task_environment["owner"]
        assignee = task_environment["assignee"]
        project = task_environment["project"]

        task = task_service.create_project_task(
            db_session, project.id, ProjectTaskCreate(title="Task Sắp Bị Xóa"), owner
        )

        # Assignee thường (vai trò MEMBER) không có quyền xóa task
        with pytest.raises(PermissionDeniedError, match="không có quyền xóa"):
            task_service.delete_task(db_session, task.id, assignee)

        # Owner xóa thành công
        task_service.delete_task(db_session, task.id, owner)
        with pytest.raises(NotFoundError):
            task_service.get_task_for_user(db_session, task.id, owner)
