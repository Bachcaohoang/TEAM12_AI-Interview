"""Bộ test kiểm chứng endpoint DELETE /tasks/{task_id} và phân quyền xóa task."""

import pytest
from fastapi.testclient import TestClient

from app.core.security import hash_password
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.task import Task
from app.models.user import User


@pytest.fixture
def delete_task_setup(db_session):
    """Tạo dự án với owner, manager, member, outsider và các task mẫu."""
    owner = User(
        email="owner_del@test.com",
        full_name="Owner Delete",
        hashed_password=hash_password("Password123"),
        role="USER",
        is_active=True,
    )
    manager = User(
        email="manager_del@test.com",
        full_name="Manager Delete",
        hashed_password=hash_password("Password123"),
        role="USER",
        is_active=True,
    )
    member = User(
        email="member_del@test.com",
        full_name="Member Delete",
        hashed_password=hash_password("Password123"),
        role="USER",
        is_active=True,
    )
    outsider = User(
        email="outsider_del@test.com",
        full_name="Outsider Delete",
        hashed_password=hash_password("Password123"),
        role="USER",
        is_active=True,
    )
    db_session.add_all([owner, manager, member, outsider])
    db_session.commit()
    for u in (owner, manager, member, outsider):
        db_session.refresh(u)

    project = Project(
        name="Dự án Delete Task",
        description="Kiểm thử phân quyền xóa công việc",
        status="in_progress",
        owner_id=owner.id,
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    db_session.add_all([
        ProjectMember(project_id=project.id, user_id=manager.id, role="MANAGER"),
        ProjectMember(project_id=project.id, user_id=member.id, role="MEMBER"),
    ])

    task1 = Task(title="Task xóa bởi Owner", status="TODO", priority="MEDIUM", project_id=project.id)
    task2 = Task(title="Task xóa bởi Manager", status="TODO", priority="HIGH", project_id=project.id)
    db_session.add_all([task1, task2])
    db_session.commit()
    db_session.refresh(task1)
    db_session.refresh(task2)

    return {"task1_id": task1.id, "task2_id": task2.id}


def get_auth_headers(client: TestClient, email: str) -> dict[str, str]:
    res = client.post(
        "/auth/login-json",
        json={"email": email, "password": "Password123"},
    )
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_regular_member_and_outsider_cannot_delete_task(client, delete_task_setup):
    """Thành viên thường (MEMBER) và user ngoài dự án bị chặn với 403 Forbidden."""
    task1_id = delete_task_setup["task1_id"]

    res_member = client.delete(
        f"/tasks/{task1_id}",
        headers=get_auth_headers(client, "member_del@test.com"),
    )
    assert res_member.status_code == 403

    res_outsider = client.delete(
        f"/tasks/{task1_id}",
        headers=get_auth_headers(client, "outsider_del@test.com"),
    )
    assert res_outsider.status_code == 403


def test_project_owner_and_manager_can_delete_task_returns_204(client, delete_task_setup):
    """Owner và Manager của dự án xóa task thành công -> 204 No Content, GET lại trả 404."""
    task1_id = delete_task_setup["task1_id"]
    task2_id = delete_task_setup["task2_id"]
    owner_headers = get_auth_headers(client, "owner_del@test.com")
    manager_headers = get_auth_headers(client, "manager_del@test.com")

    res_owner_del = client.delete(f"/tasks/{task1_id}", headers=owner_headers)
    assert res_owner_del.status_code == 204
    assert res_owner_del.content == b""

    res_get_deleted = client.get(f"/tasks/{task1_id}", headers=owner_headers)
    assert res_get_deleted.status_code == 404

    res_mgr_del = client.delete(f"/tasks/{task2_id}", headers=manager_headers)
    assert res_mgr_del.status_code == 204


def test_delete_nonexistent_task_returns_404(client, delete_task_setup):
    """Xóa task không tồn tại trả về 404 Not Found."""
    owner_headers = get_auth_headers(client, "owner_del@test.com")
    res = client.delete("/tasks/999999", headers=owner_headers)
    assert res.status_code == 404
