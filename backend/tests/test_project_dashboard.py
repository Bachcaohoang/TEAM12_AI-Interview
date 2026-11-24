"""Bộ test kiểm thử endpoint GET /projects/{id}/dashboard (Task TB8EDB8)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.main import app
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.task import Task
from app.models.user import User
from tests.conftest import TestingSessionLocal

client = TestClient(app)


def _token_for(user: User) -> str:
    return create_access_token(subject=user.id, role=user.role)


@pytest.fixture
def dashboard_world():
    db = TestingSessionLocal()
    try:
        owner = User(email="dash_owner@test.com", full_name="Dash Owner", hashed_password="x", role="USER", is_active=True)
        member = User(email="dash_member@test.com", full_name="Dash Member", hashed_password="x", role="USER", is_active=True)
        outsider = User(email="dash_outsider@test.com", full_name="Dash Outsider", hashed_password="x", role="USER", is_active=True)
        db.add_all([owner, member, outsider])
        db.commit()

        proj = Project(name="Dashboard Project", description="Test thống kê", owner_id=owner.id)
        empty_proj = Project(name="Empty Project", description="Chưa có task", owner_id=owner.id)
        db.add_all([proj, empty_proj])
        db.commit()

        db.add(ProjectMember(project_id=proj.id, user_id=member.id, role="MEMBER"))
        db.commit()

        # 4 tasks: 2 DONE (50%), 1 IN_PROGRESS, 1 TODO
        db.add_all([
            Task(title="T1", status="DONE", priority="HIGH", project_id=proj.id, assignee_id=owner.id),
            Task(title="T2", status="DONE", priority="MEDIUM", project_id=proj.id, assignee_id=member.id),
            Task(title="T3", status="IN_PROGRESS", priority="MEDIUM", project_id=proj.id, assignee_id=member.id),
            Task(title="T4", status="TODO", priority="LOW", project_id=proj.id, assignee_id=None),
        ])
        db.commit()

        return {
            "owner_token": _token_for(owner),
            "member_token": _token_for(member),
            "outsider_token": _token_for(outsider),
            "proj_id": proj.id,
            "empty_proj_id": empty_proj.id,
            "owner_id": owner.id,
            "member_id": member.id,
        }
    finally:
        db.close()


def test_dashboard_statistics_success(dashboard_world):
    """1. Thống kê chính xác tỷ lệ hoàn thành, trạng thái và phân bổ theo assignee."""
    headers = {"Authorization": f"Bearer {dashboard_world['owner_token']}"}
    res = client.get(f"/projects/{dashboard_world['proj_id']}/dashboard", headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert data["project_id"] == dashboard_world["proj_id"]
    assert data["total_tasks"] == 4
    assert data["completed_tasks"] == 2
    assert data["completion_rate"] == 50.0

    assert data["tasks_by_status"] == {
        "TODO": 1,
        "IN_PROGRESS": 1,
        "DONE": 2,
    }

    by_assignee = {item["assignee_id"]: item for item in data["tasks_by_assignee"]}
    assert by_assignee[dashboard_world["member_id"]]["total_tasks"] == 2
    assert by_assignee[dashboard_world["member_id"]]["done"] == 1
    assert by_assignee[dashboard_world["member_id"]]["in_progress"] == 1
    assert by_assignee[dashboard_world["member_id"]]["completion_rate"] == 50.0

    assert by_assignee[dashboard_world["owner_id"]]["total_tasks"] == 1
    assert by_assignee[dashboard_world["owner_id"]]["completion_rate"] == 100.0

    assert by_assignee[None]["full_name"] == "Chưa phân công"
    assert by_assignee[None]["total_tasks"] == 1


def test_dashboard_empty_project_zero_rate(dashboard_world):
    """2. Dự án chưa có task nào -> Trả về 0 và completion_rate = 0.0 (không lỗi chia cho 0)."""
    headers = {"Authorization": f"Bearer {dashboard_world['owner_token']}"}
    res = client.get(f"/projects/{dashboard_world['empty_proj_id']}/dashboard", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total_tasks"] == 0
    assert data["completed_tasks"] == 0
    assert data["completion_rate"] == 0.0
    assert data["tasks_by_assignee"] == []


def test_dashboard_member_allowed_and_outsider_forbidden(dashboard_world):
    """3. Thành viên dự án được xem (200), người ngoài dự án bị chặn (403)."""
    proj_id = dashboard_world["proj_id"]

    res_member = client.get(
        f"/projects/{proj_id}/dashboard",
        headers={"Authorization": f"Bearer {dashboard_world['member_token']}"},
    )
    assert res_member.status_code == 200

    res_outsider = client.get(
        f"/projects/{proj_id}/dashboard",
        headers={"Authorization": f"Bearer {dashboard_world['outsider_token']}"},
    )
    assert res_outsider.status_code == 403


def test_dashboard_project_not_found(dashboard_world):
    """4. Dự án không tồn tại -> Trả về 404 Not Found."""
    headers = {"Authorization": f"Bearer {dashboard_world['owner_token']}"}
    res = client.get("/projects/99999/dashboard", headers=headers)
    assert res.status_code == 404