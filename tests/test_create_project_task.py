"""Bộ test tự động cho endpoint POST /projects/{project_id}/tasks."""

import pytest
from fastapi.testclient import TestClient

from app.core.security import hash_password
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.user import User


@pytest.fixture
def project_setup(db_session):
    """Tạo dữ liệu Owner, Member, Stranger và Project mẫu."""
    owner = User(
        email="owner_task@test.com",
        full_name="Project Owner",
        hashed_password=hash_password("Password123"),
        role="USER",
        is_active=True,
    )
    member = User(
        email="member_task@test.com",
        full_name="Project Member",
        hashed_password=hash_password("Password123"),
        role="USER",
        is_active=True,
    )
    stranger = User(
        email="stranger_task@test.com",
        full_name="Stranger User",
        hashed_password=hash_password("Password123"),
        role="USER",
        is_active=True,
    )
    db_session.add_all([owner, member, stranger])
    db_session.commit()
    for u in (owner, member, stranger):
        db_session.refresh(u)

    project = Project(
        name="Dự án Test Tạo Task",
        description="Kiểm thử quyền tạo task của thành viên",
        status="in_progress",
        owner_id=owner.id,
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    membership = ProjectMember(project_id=project.id, user_id=member.id, role="MEMBER")
    db_session.add(membership)
    db_session.commit()

    return {
        "owner_id": owner.id,
        "member_id": member.id,
        "project_id": project.id,
    }


def get_auth_headers(client: TestClient, email: str) -> dict[str, str]:
    res = client.post(
        "/auth/login-json",
        json={"email": email, "password": "Password123"},
    )
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_member_can_create_task_with_due_date(client, project_setup):
    """Thành viên dự án tạo task thành công với đầy đủ title, description, due_date."""
    headers = get_auth_headers(client, "member_task@test.com")
    project_id = project_setup["project_id"]

    payload = {
        "title": "Xây dựng API tạo Task",
        "description": "Hoàn thiện endpoint POST /projects/{id}/tasks",
        "due_date": "2026-12-01T17:00:00",
    }
    res = client.post(f"/projects/{project_id}/tasks", json=payload, headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert data["title"] == "Xây dựng API tạo Task"
    assert data["description"] == "Hoàn thiện endpoint POST /projects/{id}/tasks"
    assert data["due_date"] == "2026-12-01T17:00:00"
    assert data["project_id"] == project_id
    assert data["status"] == "TODO"


def test_owner_can_create_task_minimal_fields(client, project_setup):
    """Chủ sở hữu dự án tạo task chỉ cần title (description và due_date là tùy chọn)."""
    headers = get_auth_headers(client, "owner_task@test.com")
    project_id = project_setup["project_id"]

    res = client.post(
        f"/projects/{project_id}/tasks",
        json={"title": "Task tối giản"},
        headers=headers,
    )
    assert res.status_code == 201
    data = res.json()
    assert data["title"] == "Task tối giản"
    assert data["description"] is None
    assert data["due_date"] is None


def test_stranger_cannot_create_task(client, project_setup):
    """Người dùng không thuộc dự án bị từ chối 403 Forbidden."""
    headers = get_auth_headers(client, "stranger_task@test.com")
    project_id = project_setup["project_id"]

    res = client.post(
        f"/projects/{project_id}/tasks",
        json={"title": "Task trái phép"},
        headers=headers,
    )
    assert res.status_code == 403


def test_create_task_in_nonexistent_project_returns_404(client, project_setup):
    """Dự án không tồn tại trả về 404 Not Found."""
    headers = get_auth_headers(client, "member_task@test.com")

    res = client.post(
        "/projects/999999/tasks",
        json={"title": "Task cho dự án không tồn tại"},
        headers=headers,
    )
    assert res.status_code == 404


def test_create_task_blank_title_returns_400(client, project_setup):
    """Tiêu đề chỉ chứa khoảng trắng bị từ chối 400 Bad Request."""
    headers = get_auth_headers(client, "member_task@test.com")
    project_id = project_setup["project_id"]

    res = client.post(
        f"/projects/{project_id}/tasks",
        json={"title": "    "},
        headers=headers,
    )
    assert res.status_code == 400
