"""Bộ test kiểm chứng hệ thống thông báo (Notification)."""

import pytest
from fastapi.testclient import TestClient

from app.core.security import hash_password
from app.models.project import Project
from app.models.user import User


@pytest.fixture
def notif_setup(db_session):
    """Tạo owner, member, other_user và 1 project mẫu."""
    owner = User(
        email="owner_notif@test.com",
        full_name="Owner Notif",
        hashed_password=hash_password("Password123"),
        role="USER",
        is_active=True,
    )
    member = User(
        email="member_notif@test.com",
        full_name="Member Notif",
        hashed_password=hash_password("Password123"),
        role="USER",
        is_active=True,
    )
    other = User(
        email="other_notif@test.com",
        full_name="Other Notif",
        hashed_password=hash_password("Password123"),
        role="USER",
        is_active=True,
    )
    db_session.add_all([owner, member, other])
    db_session.commit()
    for u in (owner, member, other):
        db_session.refresh(u)

    project = Project(
        name="Dự án Thông Báo",
        description="Kiểm thử notification",
        status="in_progress",
        owner_id=owner.id,
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    return {
        "owner_id": owner.id,
        "member_id": member.id,
        "other_id": other.id,
        "project_id": project.id,
    }


def get_auth_headers(client: TestClient, email: str) -> dict[str, str]:
    res = client.post(
        "/auth/login-json",
        json={"email": email, "password": "Password123"},
    )
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_notification_on_project_member_added_and_task_assigned(client, notif_setup):
    """Thêm user vào dự án và giao task mới -> user nhận đúng 2 thông báo chưa đọc."""
    owner_headers = get_auth_headers(client, "owner_notif@test.com")
    member_headers = get_auth_headers(client, "member_notif@test.com")
    project_id = notif_setup["project_id"]
    member_id = notif_setup["member_id"]

    # 1. Thêm member vào dự án -> kích hoạt thông báo PROJECT_ADDED
    res_add = client.post(
        f"/projects/{project_id}/members",
        headers=owner_headers,
        json={"user_id": member_id, "role": "MEMBER"},
    )
    assert res_add.status_code == 201

    # 2. Tạo task mới và giao cho member -> kích hoạt thông báo TASK_ASSIGNED
    res_task = client.post(
        f"/projects/{project_id}/tasks",
        headers=owner_headers,
        json={
            "title": "Thiết kế API Notification",
            "status": "TODO",
            "priority": "HIGH",
            "assignee_id": member_id,
        },
    )
    assert res_task.status_code == 201

    # Kiểm tra hộp thư thông báo của member
    res_notifs = client.get("/notifications", headers=member_headers)
    assert res_notifs.status_code == 200
    body = res_notifs.json()
    assert body["total"] == 2
    assert body["unread_count"] == 2
    types = [item["type"] for item in body["items"]]
    assert "TASK_ASSIGNED" in types
    assert "PROJECT_ADDED" in types


def test_notification_on_task_status_change_and_mark_read(client, notif_setup):
    """Đổi trạng thái task -> gửi thông báo cho bên liên quan; kiểm tra đánh dấu đã đọc & chống IDOR."""
    owner_headers = get_auth_headers(client, "owner_notif@test.com")
    member_headers = get_auth_headers(client, "member_notif@test.com")
    other_headers = get_auth_headers(client, "other_notif@test.com")
    project_id = notif_setup["project_id"]
    member_id = notif_setup["member_id"]

    client.post(
        f"/projects/{project_id}/members",
        headers=owner_headers,
        json={"user_id": member_id, "role": "MEMBER"},
    )
    res_task = client.post(
        f"/projects/{project_id}/tasks",
        headers=owner_headers,
        json={
            "title": "Triển khai WebSocket",
            "status": "TODO",
            "assignee_id": member_id,
        },
    )
    task_id = res_task.json()["id"]

    # Member cập nhật trạng thái task -> Owner nhận thông báo TASK_STATUS_CHANGED
    res_patch = client.patch(
        f"/tasks/{task_id}",
        headers=member_headers,
        json={"status": "IN_PROGRESS"},
    )
    assert res_patch.status_code == 200

    res_owner_notifs = client.get("/notifications", headers=owner_headers)
    assert res_owner_notifs.status_code == 200
    owner_data = res_owner_notifs.json()
    assert owner_data["unread_count"] == 1
    notif_id = owner_data["items"][0]["id"]
    assert owner_data["items"][0]["type"] == "TASK_STATUS_CHANGED"

    # Chống IDOR: user khác không được đánh dấu đã đọc thông báo của owner
    res_idor = client.patch(f"/notifications/{notif_id}/read", headers=other_headers)
    assert res_idor.status_code == 403

    # Owner đánh dấu đã đọc thông báo của mình
    res_read = client.patch(f"/notifications/{notif_id}/read", headers=owner_headers)
    assert res_read.status_code == 200
    assert res_read.json()["is_read"] is True

    # Member dùng read-all để đánh dấu toàn bộ thông báo của mình là đã đọc
    res_read_all = client.patch("/notifications/read-all", headers=member_headers)
    assert res_read_all.status_code == 200
    assert res_read_all.json()["updated_count"] == 2

    res_member_after = client.get("/notifications?unread_only=true", headers=member_headers)
    assert res_member_after.json()["total"] == 0
    assert res_member_after.json()["unread_count"] == 0
