"""Bộ test kiểm chứng nghiệp vụ gán Assignee cho Task (chỉ cho phép thành viên project)."""

import pytest
from fastapi.testclient import TestClient

from app.core.security import hash_password
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.task import Task
from app.models.user import User


@pytest.fixture
def assignee_setup(db_session):
    """Tạo dự án với owner, member thuộc project và outsider ngoài project."""
    owner = User(
        email="owner_assign@test.com",
        full_name="Owner Assign",
        hashed_password=hash_password("Password123"),
        role="USER",
        is_active=True,
    )
    member = User(
        email="member_assign@test.com",
        full_name="Member Assign",
        hashed_password=hash_password("Password123"),
        role="USER",
        is_active=True,
    )
    outsider = User(
        email="outsider_assign@test.com",
        full_name="Outsider Assign",
        hashed_password=hash_password("Password123"),
        role="USER",
        is_active=True,
    )
    db_session.add_all([owner, member, outsider])
    db_session.commit()
    for u in (owner, member, outsider):
        db_session.refresh(u)

    project = Project(
        name="Dự án Assignee",
        description="Kiểm thử gán người thực hiện",
        status="in_progress",
        owner_id=owner.id,
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    db_session.add(ProjectMember(project_id=project.id, user_id=member.id, role="MEMBER"))

    task = Task(
        title="Task cần giao việc",
        status="TODO",
        priority="MEDIUM",
        project_id=project.id,
        assignee_id=None,
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    return {
        "project_id": project.id,
        "task_id": task.id,
        "owner_id": owner.id,
        "member_id": member.id,
        "outsider_id": outsider.id,
    }


def get_auth_headers(client: TestClient, email: str) -> dict[str, str]:
    res = client.post(
        "/auth/login-json",
        json={"email": email, "password": "Password123"},
    )
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_assign_project_member_via_patch_succeeds(client, assignee_setup):
    """Gán assignee là thành viên của project qua PATCH /tasks/{id} -> 200 OK."""
    headers = get_auth_headers(client, "owner_assign@test.com")
    task_id = assignee_setup["task_id"]
    member_id = assignee_setup["member_id"]

    res = client.patch(
        f"/tasks/{task_id}",
        headers=headers,
        json={"assignee_id": member_id},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["assignee_id"] == member_id
    assert data["assignee"]["id"] == member_id


def test_assign_outsider_via_patch_rejected_with_400(client, assignee_setup):
    """Không cho gán user ngoài project qua PATCH /tasks/{id} -> 400 Bad Request."""
    headers = get_auth_headers(client, "owner_assign@test.com")
    task_id = assignee_setup["task_id"]
    outsider_id = assignee_setup["outsider_id"]

    res = client.patch(
        f"/tasks/{task_id}",
        headers=headers,
        json={"assignee_id": outsider_id},
    )
    assert res.status_code == 400


def test_create_task_with_outsider_assignee_rejected_with_400(client, assignee_setup):
    """Không cho gán user ngoài project khi tạo task mới POST /projects/{id}/tasks -> 400."""
    headers = get_auth_headers(client, "owner_assign@test.com")
    project_id = assignee_setup["project_id"]
    outsider_id = assignee_setup["outsider_id"]

    res = client.post(
        f"/projects/{project_id}/tasks",
        headers=headers,
        json={"title": "Task giao sai người", "assignee_id": outsider_id},
    )
    assert res.status_code == 400


def test_create_task_with_member_assignee_succeeds(client, assignee_setup):
    """Tạo task mới và gán cho thành viên thuộc project -> 201 Created."""
    headers = get_auth_headers(client, "owner_assign@test.com")
    project_id = assignee_setup["project_id"]
    member_id = assignee_setup["member_id"]

    res = client.post(
        f"/projects/{project_id}/tasks",
        headers=headers,
        json={"title": "Task giao đúng thành viên", "assignee_id": member_id},
    )
    assert res.status_code == 201
    assert res.json()["assignee_id"] == member_id
