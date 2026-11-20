"""Bộ test kiểm chứng endpoint PATCH /tasks/{task_id}."""

import pytest
from fastapi.testclient import TestClient

from app.core.security import hash_password
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.task import Task
from app.models.user import User


@pytest.fixture
def task_update_setup(db_session):
    """Tạo dữ liệu dự án, thành viên và task đầy đủ thông tin ban đầu."""
    owner = User(
        email="owner_upd@test.com",
        full_name="Owner Update",
        hashed_password=hash_password("Password123"),
        role="USER",
        is_active=True,
    )
    member = User(
        email="member_upd@test.com",
        full_name="Member Update",
        hashed_password=hash_password("Password123"),
        role="USER",
        is_active=True,
    )
    outsider = User(
        email="outsider_upd@test.com",
        full_name="Outsider Update",
        hashed_password=hash_password("Password123"),
        role="USER",
        is_active=True,
    )
    db_session.add_all([owner, member, outsider])
    db_session.commit()
    for u in (owner, member, outsider):
        db_session.refresh(u)

    project = Project(
        name="Dự án Update",
        description="Dự án kiểm thử cập nhật task",
        status="in_progress",
        owner_id=owner.id,
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    db_session.add(ProjectMember(project_id=project.id, user_id=member.id, role="MEMBER"))

    task = Task(
        title="Tiêu đề gốc",
        description="Mô tả gốc cần giữ nguyên",
        status="TODO",
        priority="HIGH",
        project_id=project.id,
        assignee_id=member.id,
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    return {
        "task_id": task.id,
        "member_id": member.id,
        "owner_id": owner.id,
    }


def get_auth_headers(client: TestClient, email: str) -> dict[str, str]:
    res = client.post(
        "/auth/login-json",
        json={"email": email, "password": "Password123"},
    )
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_partial_update_preserves_omitted_fields(client, task_update_setup):
    """Chỉ gửi status và title mới -> cập nhật đúng 2 trường đó, giữ nguyên các trường không gửi lên."""
    headers = get_auth_headers(client, "member_upd@test.com")
    task_id = task_update_setup["task_id"]

    res = client.patch(
        f"/tasks/{task_id}",
        headers=headers,
        json={"title": "Tiêu đề đã sửa", "status": "in_progress"},
    )
    assert res.status_code == 200
    data = res.json()

    assert data["title"] == "Tiêu đề đã sửa"
    assert data["status"] == "IN_PROGRESS"
    assert data["description"] == "Mô tả gốc cần giữ nguyên"
    assert data["priority"] == "HIGH"
    assert data["assignee_id"] == task_update_setup["member_id"]


def test_update_task_invalid_status_or_blank_title_returns_400(client, task_update_setup):
    """Gửi giá trị status không hợp lệ hoặc title chỉ có khoảng trắng trả về 400 Bad Request."""
    headers = get_auth_headers(client, "member_upd@test.com")
    task_id = task_update_setup["task_id"]

    res_status = client.patch(
        f"/tasks/{task_id}",
        headers=headers,
        json={"status": "INVALID_STATUS"},
    )
    assert res_status.status_code == 400

    res_title = client.patch(
        f"/tasks/{task_id}",
        headers=headers,
        json={"title": "   "},
    )
    assert res_title.status_code == 400


def test_outsider_cannot_update_task(client, task_update_setup):
    """User không thuộc project bị từ chối cập nhật task (403 Forbidden)."""
    headers = get_auth_headers(client, "outsider_upd@test.com")
    task_id = task_update_setup["task_id"]

    res = client.patch(
        f"/tasks/{task_id}",
        headers=headers,
        json={"title": "Sửa trái phép"},
    )
    assert res.status_code == 403


def test_update_nonexistent_task_returns_404(client, task_update_setup):
    """Cập nhật task không tồn tại trả về 404 Not Found."""
    headers = get_auth_headers(client, "member_upd@test.com")

    res = client.patch(
        "/tasks/999999",
        headers=headers,
        json={"status": "DONE"},
    )
    assert res.status_code == 404
