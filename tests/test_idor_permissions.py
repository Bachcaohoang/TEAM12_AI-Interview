"""Bộ test kiểm thử phân quyền Owner / Member / Assignee và chống lỗ hổng IDOR (Task TB8EDA3)."""

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
def rbac_world():
    """
    Tạo môi trường 2 dự án để kiểm thử IDOR & phân quyền:
    - Project A:
        + owner_a: Chủ sở hữu Project A
        + assignee_a: Thành viên Project A, được giao Task A1
        + member_a: Thành viên Project A, KHÔNG được giao Task A1
    - Project B:
        + owner_b: Chủ sở hữu Project B (người ngoài đối với Project A -> test IDOR)
    """
    db = TestingSessionLocal()
    try:
        owner_a = User(email="owner_a@test.com", full_name="Owner A", hashed_password="x", role="USER", is_active=True)
        assignee_a = User(email="assignee_a@test.com", full_name="Assignee A", hashed_password="x", role="USER", is_active=True)
        member_a = User(email="member_a@test.com", full_name="Member A", hashed_password="x", role="USER", is_active=True)
        owner_b = User(email="owner_b@test.com", full_name="Owner B", hashed_password="x", role="USER", is_active=True)

        db.add_all([owner_a, assignee_a, member_a, owner_b])
        db.commit()

        proj_a = Project(name="Project A", description="Dự án A", owner_id=owner_a.id)
        proj_b = Project(name="Project B", description="Dự án B", owner_id=owner_b.id)
        db.add_all([proj_a, proj_b])
        db.commit()

        db.add_all([
            ProjectMember(project_id=proj_a.id, user_id=assignee_a.id, role="MEMBER"),
            ProjectMember(project_id=proj_a.id, user_id=member_a.id, role="MEMBER"),
        ])
        db.commit()

        task_a1 = Task(
            title="Task A1 của Assignee A",
            description="Mô tả ban đầu",
            status="TODO",
            priority="MEDIUM",
            project_id=proj_a.id,
            assignee_id=assignee_a.id,
        )
        db.add(task_a1)
        db.commit()

        return {
            "owner_a_token": _token_for(owner_a),
            "assignee_a_token": _token_for(assignee_a),
            "member_a_token": _token_for(member_a),
            "owner_b_token": _token_for(owner_b),
            "proj_a_id": proj_a.id,
            "proj_b_id": proj_b.id,
            "task_a1_id": task_a1.id,
            "member_a_id": member_a.id,
        }
    finally:
        db.close()


# ==============================================================================
# 1. CHỐNG IDOR TRÊN PROJECT & PROJECT MEMBERS
# ==============================================================================

def test_idor_outsider_cannot_access_other_project_resources(rbac_world):
    """Owner B (thuộc Project B) cố tình đổi ID sang Project A -> Bị chặn 403 toàn bộ."""
    headers_b = {"Authorization": f"Bearer {rbac_world['owner_b_token']}"}
    proj_a_id = rbac_world["proj_a_id"]

    assert client.get(f"/projects/{proj_a_id}", headers=headers_b).status_code == 403
    assert client.put(f"/projects/{proj_a_id}", json={"name": "Hacked"}, headers=headers_b).status_code == 403
    assert client.delete(f"/projects/{proj_a_id}", headers=headers_b).status_code == 403
    assert client.get(f"/projects/{proj_a_id}/members", headers=headers_b).status_code == 403
    assert client.post(
        f"/projects/{proj_a_id}/members",
        json={"user_id": rbac_world["member_a_id"], "role": "MEMBER"},
        headers=headers_b,
    ).status_code == 403


def test_member_vs_owner_project_permissions(rbac_world):
    """Member xem được danh sách thành viên dự án (200), nhưng không được sửa/xóa dự án hay thêm thành viên (403)."""
    headers_member = {"Authorization": f"Bearer {rbac_world['member_a_token']}"}
    proj_a_id = rbac_world["proj_a_id"]

    assert client.get(f"/projects/{proj_a_id}/members", headers=headers_member).status_code == 200
    assert client.put(f"/projects/{proj_a_id}", json={"name": "Member Rename"}, headers=headers_member).status_code == 403
    assert client.delete(f"/projects/{proj_a_id}", headers=headers_member).status_code == 403


# ==============================================================================
# 2. CHỐNG IDOR & PHÂN QUYỀN OWNER / MEMBER / ASSIGNEE TRÊN TASK
# ==============================================================================

def test_idor_outsider_cannot_read_update_or_delete_task(rbac_world):
    """Owner B (người ngoài Project A) truy cập Task A1 của Project A -> Bị chặn 403."""
    headers_b = {"Authorization": f"Bearer {rbac_world['owner_b_token']}"}
    task_id = rbac_world["task_a1_id"]
    proj_a_id = rbac_world["proj_a_id"]

    assert client.get(f"/projects/{proj_a_id}/tasks", headers=headers_b).status_code == 403
    assert client.get(f"/tasks/{task_id}", headers=headers_b).status_code == 403
    assert client.patch(f"/tasks/{task_id}", json={"status": "IN_PROGRESS"}, headers=headers_b).status_code == 403
    assert client.delete(f"/tasks/{task_id}", headers=headers_b).status_code == 403


def test_member_not_assignee_can_view_but_cannot_modify_or_delete_task(rbac_world):
    """Member A thuộc dự án nên xem được Task A1 (200), nhưng không phải Assignee/Owner nên sửa/xóa bị 403."""
    headers_member = {"Authorization": f"Bearer {rbac_world['member_a_token']}"}
    task_id = rbac_world["task_a1_id"]

    assert client.get(f"/tasks/{task_id}", headers=headers_member).status_code == 200
    assert client.patch(f"/tasks/{task_id}", json={"status": "IN_PROGRESS"}, headers=headers_member).status_code == 403
    assert client.delete(f"/tasks/{task_id}", headers=headers_member).status_code == 403


def test_assignee_can_update_own_status_but_cannot_reassign_or_delete(rbac_world):
    """Assignee A cập nhật được status/description của task mình (200), nhưng không được đổi assignee/title hay xóa task (403)."""
    headers_assignee = {"Authorization": f"Bearer {rbac_world['assignee_a_token']}"}
    task_id = rbac_world["task_a1_id"]

    # Được phép cập nhật tiến độ của chính mình
    ok_res = client.patch(
        f"/tasks/{task_id}",
        json={"status": "IN_PROGRESS", "description": "Đang làm"},
        headers=headers_assignee,
    )
    assert ok_res.status_code == 200
    assert ok_res.json()["status"] == "IN_PROGRESS"

    # Bị chặn khi cố đổi assignee hoặc title
    assert client.patch(
        f"/tasks/{task_id}",
        json={"assignee_id": rbac_world["member_a_id"]},
        headers=headers_assignee,
    ).status_code == 403
    assert client.patch(
        f"/tasks/{task_id}",
        json={"title": "Tự đổi tên task"},
        headers=headers_assignee,
    ).status_code == 403

    # Bị chặn khi cố xóa task
    assert client.delete(f"/tasks/{task_id}", headers=headers_assignee).status_code == 403


def test_owner_has_full_control_over_project_tasks(rbac_world):
    """Owner A có toàn quyền đổi assignee, sửa tiêu đề và xóa task trong Project A."""
    headers_owner = {"Authorization": f"Bearer {rbac_world['owner_a_token']}"}
    task_id = rbac_world["task_a1_id"]

    reassign_res = client.patch(
        f"/tasks/{task_id}",
        json={"title": "Owner cập nhật", "assignee_id": rbac_world["member_a_id"]},
        headers=headers_owner,
    )
    assert reassign_res.status_code == 200
    assert reassign_res.json()["title"] == "Owner cập nhật"

    del_res = client.delete(f"/tasks/{task_id}", headers=headers_owner)
    assert del_res.status_code == 204