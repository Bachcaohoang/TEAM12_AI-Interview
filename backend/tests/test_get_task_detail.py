"""Bộ test kiểm chứng endpoint GET /tasks/{task_id}."""

import pytest
from fastapi.testclient import TestClient

from app.core.security import hash_password
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.task import Task
from app.models.user import User


@pytest.fixture
def task_access_setup(db_session):
    """Tạo 2 user (1 thuộc project, 1 ngoài project) và 1 task để test phân quyền."""
    owner = User(
        email="owner_detail@test.com",
        full_name="Owner Detail",
        hashed_password=hash_password("Password123"),
        role="USER",
        is_active=True,
    )
    member = User(
        email="member_detail@test.com",
        full_name="Member Detail",
        hashed_password=hash_password("Password123"),
        role="USER",
        is_active=True,
    )
    outsider = User(
        email="outsider_detail@test.com",
        full_name="Outsider Detail",
        hashed_password=hash_password("Password123"),
        role="USER",
        is_active=True,
    )
    db_session.add_all([owner, member, outsider])
    db_session.commit()
    for u in (owner, member, outsider):
        db_session.refresh(u)

    project = Project(
        name="Dự án Chi Tiết",
        description="Dự án kiểm thử chi tiết task",
        status="in_progress",
        owner_id=owner.id,
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    db_session.add(ProjectMember(project_id=project.id, user_id=member.id, role="MEMBER"))

    task = Task(
        title="Task Nội Bộ",
        description="Mô tả chi tiết task",
        status="TODO",
        priority="HIGH",
        project_id=project.id,
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    return {
        "task_id": task.id,
        "project_id": project.id,
    }


def get_auth_headers(client: TestClient, email: str) -> dict[str, str]:
    res = client.post(
        "/auth/login-json",
        json={"email": email, "password": "Password123"},
    )
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_project_member_can_get_task_detail(client, task_access_setup):
    """Thành viên thuộc project lấy được chi tiết task (200 OK)."""
    headers = get_auth_headers(client, "member_detail@test.com")
    task_id = task_access_setup["task_id"]

    res = client.get(f"/tasks/{task_id}", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == task_id
    assert data["title"] == "Task Nội Bộ"
    assert data["project_id"] == task_access_setup["project_id"]


def test_outsider_cannot_get_task_detail(client, task_access_setup):
    """User không thuộc project bị từ chối truy cập chi tiết task (403 Forbidden)."""
    headers = get_auth_headers(client, "outsider_detail@test.com")
    task_id = task_access_setup["task_id"]

    res = client.get(f"/tasks/{task_id}", headers=headers)
    assert res.status_code == 403


def test_get_nonexistent_task_returns_404(client, task_access_setup):
    """Truy vấn task không tồn tại trả về 404 Not Found."""
    headers = get_auth_headers(client, "member_detail@test.com")

    res = client.get("/tasks/999999", headers=headers)
    assert res.status_code == 404
