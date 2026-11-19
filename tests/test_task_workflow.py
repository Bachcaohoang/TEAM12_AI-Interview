"""Bộ test kiểm chứng workflow chuyển trạng thái (TODO/IN_PROGRESS/DONE) và priority (LOW/MEDIUM/HIGH)."""

import pytest
from fastapi.testclient import TestClient

from app.core.security import hash_password
from app.models.project import Project
from app.models.task import Task
from app.models.user import User


@pytest.fixture
def workflow_setup(db_session):
    """Tạo dự án và task khởi tạo ở trạng thái TODO, priority MEDIUM."""
    owner = User(
        email="owner_wf@test.com",
        full_name="Owner Workflow",
        hashed_password=hash_password("Password123"),
        role="USER",
        is_active=True,
    )
    db_session.add(owner)
    db_session.commit()
    db_session.refresh(owner)

    project = Project(
        name="Dự án Workflow",
        description="Kiểm thử workflow trạng thái và độ ưu tiên",
        status="in_progress",
        owner_id=owner.id,
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    task = Task(
        title="Task kiểm thử workflow",
        status="TODO",
        priority="MEDIUM",
        project_id=project.id,
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    return {"project_id": project.id, "task_id": task.id}


def get_auth_headers(client: TestClient, email: str) -> dict[str, str]:
    res = client.post(
        "/auth/login-json",
        json={"email": email, "password": "Password123"},
    )
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_valid_status_lifecycle_transitions(client, workflow_setup):
    """Kiểm tra luồng chuyển trạng thái hợp lệ: TODO -> IN_PROGRESS -> DONE -> IN_PROGRESS -> TODO."""
    headers = get_auth_headers(client, "owner_wf@test.com")
    task_id = workflow_setup["task_id"]

    # TODO -> IN_PROGRESS
    r1 = client.patch(f"/tasks/{task_id}", headers=headers, json={"status": "IN_PROGRESS"})
    assert r1.status_code == 200
    assert r1.json()["status"] == "IN_PROGRESS"

    # IN_PROGRESS -> DONE
    r2 = client.patch(f"/tasks/{task_id}", headers=headers, json={"status": "DONE"})
    assert r2.status_code == 200
    assert r2.json()["status"] == "DONE"

    # DONE -> IN_PROGRESS (mở lại task)
    r3 = client.patch(f"/tasks/{task_id}", headers=headers, json={"status": "IN_PROGRESS"})
    assert r3.status_code == 200
    assert r3.json()["status"] == "IN_PROGRESS"

    # IN_PROGRESS -> TODO
    r4 = client.patch(f"/tasks/{task_id}", headers=headers, json={"status": "TODO"})
    assert r4.status_code == 200
    assert r4.json()["status"] == "TODO"


def test_invalid_status_jumps_return_400(client, workflow_setup):
    """Chặn nhảy thẳng TODO -> DONE và DONE -> TODO với mã 400 Bad Request."""
    headers = get_auth_headers(client, "owner_wf@test.com")
    task_id = workflow_setup["task_id"]

    # Đang ở TODO -> nhảy thẳng sang DONE bị chặn
    r_skip = client.patch(f"/tasks/{task_id}", headers=headers, json={"status": "DONE"})
    assert r_skip.status_code == 400

    # Chuyển hợp lệ TODO -> IN_PROGRESS -> DONE
    assert client.patch(f"/tasks/{task_id}", headers=headers, json={"status": "IN_PROGRESS"}).status_code == 200
    assert client.patch(f"/tasks/{task_id}", headers=headers, json={"status": "DONE"}).status_code == 200

    # Đang ở DONE -> nhảy thẳng về TODO bị chặn
    r_reopen_skip = client.patch(f"/tasks/{task_id}", headers=headers, json={"status": "TODO"})
    assert r_reopen_skip.status_code == 400


def test_priority_validation_values(client, workflow_setup):
    """Kiểm tra cập nhật các giá trị priority hợp lệ (LOW, MEDIUM, HIGH) và từ chối giá trị sai."""
    headers = get_auth_headers(client, "owner_wf@test.com")
    task_id = workflow_setup["task_id"]

    for valid_prio in ("LOW", "HIGH", "MEDIUM"):
        res = client.patch(f"/tasks/{task_id}", headers=headers, json={"priority": valid_prio})
        assert res.status_code == 200
        assert res.json()["priority"] == valid_prio

    res_invalid = client.patch(f"/tasks/{task_id}", headers=headers, json={"priority": "URGENT"})
    assert res_invalid.status_code == 400
