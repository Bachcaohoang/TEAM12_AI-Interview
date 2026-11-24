"""Bộ test kiểm chứng endpoint GET /projects/{project_id}/tasks."""

import pytest
from fastapi.testclient import TestClient

from app.core.security import hash_password
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.task import Task
from app.models.user import User


@pytest.fixture
def two_projects_setup(db_session):
    """Tạo 2 dự án độc lập với danh sách task riêng để kiểm tra tính cô lập dữ liệu."""
    owner_a = User(
        email="owner_a@test.com",
        full_name="Owner A",
        hashed_password=hash_password("Password123"),
        role="USER",
        is_active=True,
    )
    member_a = User(
        email="member_a@test.com",
        full_name="Member A",
        hashed_password=hash_password("Password123"),
        role="USER",
        is_active=True,
    )
    owner_b = User(
        email="owner_b@test.com",
        full_name="Owner B",
        hashed_password=hash_password("Password123"),
        role="USER",
        is_active=True,
    )
    db_session.add_all([owner_a, member_a, owner_b])
    db_session.commit()
    for u in (owner_a, member_a, owner_b):
        db_session.refresh(u)

    project_a = Project(
        name="Dự án A",
        description="Dự án nội bộ A",
        status="in_progress",
        owner_id=owner_a.id,
    )
    project_b = Project(
        name="Dự án B",
        description="Dự án bí mật B",
        status="in_progress",
        owner_id=owner_b.id,
    )
    db_session.add_all([project_a, project_b])
    db_session.commit()
    db_session.refresh(project_a)
    db_session.refresh(project_b)

    db_session.add(ProjectMember(project_id=project_a.id, user_id=member_a.id, role="MEMBER"))

    task_a1 = Task(title="Task A1", status="TODO", priority="HIGH", project_id=project_a.id)
    task_a2 = Task(title="Task A2", status="DONE", priority="LOW", project_id=project_a.id)
    task_b1 = Task(title="Task Bí Mật B1", status="TODO", priority="HIGH", project_id=project_b.id)
    db_session.add_all([task_a1, task_a2, task_b1])
    db_session.commit()

    return {
        "project_a_id": project_a.id,
        "project_b_id": project_b.id,
    }


def get_auth_headers(client: TestClient, email: str) -> dict[str, str]:
    res = client.post(
        "/auth/login-json",
        json={"email": email, "password": "Password123"},
    )
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_list_tasks_returns_only_project_tasks_without_leaking_others(client, two_projects_setup):
    """Chỉ trả về task thuộc project_a, không lộ bất kỳ task nào của project_b."""
    headers = get_auth_headers(client, "member_a@test.com")
    project_a_id = two_projects_setup["project_a_id"]

    res = client.get(f"/projects/{project_a_id}/tasks", headers=headers)
    assert res.status_code == 200
    data = res.json()["items"]

    assert len(data) == 2
    titles = {item["title"] for item in data}
    assert titles == {"Task A1", "Task A2"}
    assert "Task Bí Mật B1" not in titles
    assert all(item["project_id"] == project_a_id for item in data)


def test_member_cannot_view_other_project_tasks(client, two_projects_setup):
    """Thành viên dự án A truy cập danh sách task dự án B bị từ chối 403 Forbidden."""
    headers = get_auth_headers(client, "member_a@test.com")
    project_b_id = two_projects_setup["project_b_id"]

    res = client.get(f"/projects/{project_b_id}/tasks", headers=headers)
    assert res.status_code == 403


def test_list_tasks_nonexistent_project_returns_404(client, two_projects_setup):
    """Truy vấn danh sách task của project không tồn tại trả về 404 Not Found."""
    headers = get_auth_headers(client, "member_a@test.com")

    res = client.get("/projects/999999/tasks", headers=headers)
    assert res.status_code == 404
