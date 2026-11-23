"""Bộ test kiểm chứng quản lý due_date và cờ cảnh báo is_overdue."""

from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient

from app.core.security import hash_password
from app.models.project import Project
from app.models.task import Task
from app.models.user import User


@pytest.fixture
def due_date_setup(db_session):
    """Tạo dữ liệu dự án, task trễ hạn (chưa DONE) và task trễ hạn (đã DONE)."""
    owner = User(
        email="owner_due@test.com",
        full_name="Owner DueDate",
        hashed_password=hash_password("Password123"),
        role="USER",
        is_active=True,
    )
    db_session.add(owner)
    db_session.commit()
    db_session.refresh(owner)

    project = Project(
        name="Dự án Due Date",
        description="Kiểm thử hạn chót và cờ cảnh báo trễ hạn",
        status="in_progress",
        owner_id=owner.id,
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)

    overdue_task = Task(
        title="Task đã quá hạn chưa xong",
        status="IN_PROGRESS",
        priority="HIGH",
        due_date=now_utc - timedelta(days=2),
        project_id=project.id,
    )
    done_past_task = Task(
        title="Task quá hạn nhưng đã DONE",
        status="DONE",
        priority="MEDIUM",
        due_date=now_utc - timedelta(days=2),
        project_id=project.id,
    )
    db_session.add_all([overdue_task, done_past_task])
    db_session.commit()
    db_session.refresh(overdue_task)
    db_session.refresh(done_past_task)

    return {
        "project_id": project.id,
        "overdue_task_id": overdue_task.id,
        "done_past_task_id": done_past_task.id,
    }


def get_auth_headers(client: TestClient, email: str) -> dict[str, str]:
    res = client.post(
        "/auth/login-json",
        json={"email": email, "password": "Password123"},
    )
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_and_update_due_date_in_past_rejected_with_400(client, due_date_setup):
    """Không cho phép đặt due_date trong quá khứ khi tạo mới hoặc cập nhật task (400)."""
    headers = get_auth_headers(client, "owner_due@test.com")
    project_id = due_date_setup["project_id"]
    past_iso = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()

    res_create = client.post(
        f"/projects/{project_id}/tasks",
        headers=headers,
        json={"title": "Task hạn quá khứ", "due_date": past_iso},
    )
    assert res_create.status_code == 400

    res_patch = client.patch(
        f"/tasks/{due_date_setup['overdue_task_id']}",
        headers=headers,
        json={"due_date": past_iso},
    )
    assert res_patch.status_code == 400


def test_create_task_with_future_due_date_not_overdue(client, due_date_setup):
    """Tạo task với due_date hợp lệ trong tương lai -> 201 Created, is_overdue=False."""
    headers = get_auth_headers(client, "owner_due@test.com")
    project_id = due_date_setup["project_id"]
    future_iso = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()

    res = client.post(
        f"/projects/{project_id}/tasks",
        headers=headers,
        json={"title": "Task hạn tương lai", "due_date": future_iso},
    )
    assert res.status_code == 201
    data = res.json()
    assert data["due_date"] is not None
    assert data["is_overdue"] is False


def test_is_overdue_flag_for_overdue_and_done_tasks(client, due_date_setup):
    """Task quá hạn chưa DONE trả về is_overdue=True; task đã DONE trả về is_overdue=False."""
    headers = get_auth_headers(client, "owner_due@test.com")

    res_overdue = client.get(f"/tasks/{due_date_setup['overdue_task_id']}", headers=headers)
    assert res_overdue.status_code == 200
    assert res_overdue.json()["is_overdue"] is True

    res_done = client.get(f"/tasks/{due_date_setup['done_past_task_id']}", headers=headers)
    assert res_done.status_code == 200
    assert res_done.json()["is_overdue"] is False

    # Khi chuyển task quá hạn sang DONE -> is_overdue chuyển thành False
    res_complete = client.patch(
        f"/tasks/{due_date_setup['overdue_task_id']}",
        headers=headers,
        json={"status": "DONE"},
    )
    assert res_complete.status_code == 200
    assert res_complete.json()["is_overdue"] is False
