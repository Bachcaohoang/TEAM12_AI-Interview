"""Kiểm thử Activity Log, Comment Task và Attachment."""

import pytest
from fastapi.testclient import TestClient

from app.core.security import hash_password
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.user import User


@pytest.fixture
def setup_users(db_session):
    owner = User(
        email="owner_aca@test.com",
        full_name="Owner ACA",
        hashed_password=hash_password("Password123"),
        role="USER",
        is_active=True,
    )
    member = User(
        email="member_aca@test.com",
        full_name="Member ACA",
        hashed_password=hash_password("Password123"),
        role="USER",
        is_active=True,
    )
    stranger = User(
        email="stranger_aca@test.com",
        full_name="Stranger ACA",
        hashed_password=hash_password("Password123"),
        role="USER",
        is_active=True,
    )
    admin = User(
        email="admin_aca@test.com",
        full_name="Admin ACA",
        hashed_password=hash_password("Password123"),
        role="ADMIN",
        is_active=True,
    )
    db_session.add_all([owner, member, stranger, admin])
    db_session.commit()
    for user in (owner, member, stranger, admin):
        db_session.refresh(user)

    project = Project(
        name="Dự án ACA",
        description="Test activity comment attachment",
        status="in_progress",
        owner_id=owner.id,
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    db_session.add(ProjectMember(project_id=project.id, user_id=member.id, role="MEMBER"))
    db_session.commit()

    return {"project_id": project.id}


def auth_headers(client: TestClient, email: str) -> dict[str, str]:
    res = client.post("/auth/login-json", json={"email": email, "password": "Password123"})
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def create_task(client: TestClient, headers: dict, project_id: int, title: str = "Task ACA") -> int:
    res = client.post(
        f"/projects/{project_id}/tasks",
        json={"title": title, "description": "Mô tả task"},
        headers=headers,
    )
    assert res.status_code == 201, res.text
    return res.json()["id"]


def test_unauthenticated_activity_comment_attachment(client, setup_users):
    project_id = setup_users["project_id"]
    assert client.get(f"/projects/{project_id}/activities").status_code == 401
    assert client.get("/tasks/1/comments").status_code == 401
    assert client.get("/tasks/1/attachments").status_code == 401


def test_activity_log_project_and_task_lifecycle(client, setup_users):
    project_id = setup_users["project_id"]
    owner = auth_headers(client, "owner_aca@test.com")
    stranger = auth_headers(client, "stranger_aca@test.com")

    forbidden = client.get(f"/projects/{project_id}/activities", headers=stranger)
    assert forbidden.status_code == 403

    create_res = client.post(
        "/projects",
        json={"name": "Dự án mới ACA", "description": "desc", "status": "in_progress"},
        headers=owner,
    )
    assert create_res.status_code == 201
    new_project_id = create_res.json()["id"]

    client.put(
        f"/projects/{new_project_id}",
        json={"description": "updated"},
        headers=owner,
    )
    task_id = create_task(client, owner, new_project_id, "Task log")
    client.put(f"/tasks/{task_id}", json={"title": "Task log updated"}, headers=owner)
    client.patch(f"/tasks/{task_id}/status", json={"status": "IN_PROGRESS"}, headers=owner)
    client.delete(f"/tasks/{task_id}", headers=owner)

    activities = client.get(
        f"/projects/{new_project_id}/activities?page=1&page_size=10",
        headers=owner,
    )
    assert activities.status_code == 200
    body = activities.json()
    assert body["total"] >= 5
    assert "items" in body
    actions = {item["action"] for item in body["items"]}
    assert "PROJECT_CREATED" in actions
    assert "PROJECT_UPDATED" in actions
    assert "TASK_CREATED" in actions
    assert "TASK_UPDATED" in actions
    assert "TASK_STATUS_CHANGED" in actions
    assert "TASK_DELETED" in actions

    invalid_page = client.get(
        f"/projects/{new_project_id}/activities?page=0",
        headers=owner,
    )
    assert invalid_page.status_code == 400


def test_comment_crud_auth_and_pagination(client, setup_users):
    project_id = setup_users["project_id"]
    owner = auth_headers(client, "owner_aca@test.com")
    member = auth_headers(client, "member_aca@test.com")
    stranger = auth_headers(client, "stranger_aca@test.com")
    admin = auth_headers(client, "admin_aca@test.com")

    task_id = create_task(client, owner, project_id)

    empty = client.post(
        f"/tasks/{task_id}/comments",
        json={"content": "   "},
        headers=member,
    )
    assert empty.status_code == 400

    created = client.post(
        f"/tasks/{task_id}/comments",
        json={"content": "Bình luận của member"},
        headers=member,
    )
    assert created.status_code == 201
    comment_id = created.json()["id"]
    assert created.json()["user_id"] is not None

    owner_comment = client.post(
        f"/tasks/{task_id}/comments",
        json={"content": "Bình luận owner"},
        headers=owner,
    )
    assert owner_comment.status_code == 201

    forbidden_create = client.post(
        f"/tasks/{task_id}/comments",
        json={"content": "stranger"},
        headers=stranger,
    )
    assert forbidden_create.status_code == 403

    listed = client.get(f"/tasks/{task_id}/comments?page=1&page_size=1", headers=owner)
    assert listed.status_code == 200
    data = listed.json()
    assert data["total"] == 2
    assert data["page_size"] == 1
    assert len(data["items"]) == 1
    assert data["has_next"] is True

    owner_edit_member = client.put(
        f"/comments/{comment_id}",
        json={"content": "owner sửa comment member"},
        headers=owner,
    )
    assert owner_edit_member.status_code == 403

    member_edit = client.put(
        f"/comments/{comment_id}",
        json={"content": "member sửa comment"},
        headers=member,
    )
    assert member_edit.status_code == 200
    assert member_edit.json()["content"] == "member sửa comment"

    admin_edit = client.put(
        f"/comments/{comment_id}",
        json={"content": "admin sửa comment"},
        headers=admin,
    )
    assert admin_edit.status_code == 200

    member_delete_owner = client.delete(
        f"/comments/{owner_comment.json()['id']}",
        headers=member,
    )
    assert member_delete_owner.status_code == 403

    admin_delete = client.delete(f"/comments/{comment_id}", headers=admin)
    assert admin_delete.status_code == 204

    missing = client.get(f"/comments/{comment_id}", headers=owner)
    assert missing.status_code == 404

    activities = client.get(f"/projects/{project_id}/activities", headers=owner)
    actions = {item["action"] for item in activities.json()["items"]}
    assert "COMMENT_CREATED" in actions
    assert "COMMENT_UPDATED" in actions
    assert "COMMENT_DELETED" in actions


def test_attachment_upload_download_delete_and_validation(client, setup_users):
    project_id = setup_users["project_id"]
    owner = auth_headers(client, "owner_aca@test.com")
    member = auth_headers(client, "member_aca@test.com")
    stranger = auth_headers(client, "stranger_aca@test.com")
    admin = auth_headers(client, "admin_aca@test.com")
    task_id = create_task(client, owner, project_id, "Task file")

    bad_ext = client.post(
        f"/tasks/{task_id}/attachments",
        files={"file": ("malware.exe", b"abc", "application/octet-stream")},
        headers=member,
    )
    assert bad_ext.status_code == 400

    empty = client.post(
        f"/tasks/{task_id}/attachments",
        files={"file": ("empty.txt", b"", "text/plain")},
        headers=member,
    )
    assert empty.status_code == 400

    traversal = client.post(
        f"/tasks/{task_id}/attachments",
        files={"file": ("../../secret.txt", b"hello-file", "text/plain")},
        headers=member,
    )
    assert traversal.status_code == 201
    assert traversal.json()["filename"] == "secret.txt"
    assert ".." not in traversal.json().get("filename", "")

    uploaded = client.post(
        f"/tasks/{task_id}/attachments",
        files={"file": ("note.txt", b"hello-file", "text/plain")},
        headers=member,
    )
    assert uploaded.status_code == 201
    attachment_id = uploaded.json()["id"]
    assert uploaded.json()["file_size"] == len(b"hello-file")

    listed = client.get(f"/tasks/{task_id}/attachments", headers=owner)
    assert listed.status_code == 200
    assert listed.json()["total"] >= 1

    forbidden_list = client.get(f"/tasks/{task_id}/attachments", headers=stranger)
    assert forbidden_list.status_code == 403

    download = client.get(f"/attachments/{attachment_id}/download", headers=owner)
    assert download.status_code == 200
    assert download.content == b"hello-file"

    forbidden_download = client.get(
        f"/attachments/{attachment_id}/download",
        headers=stranger,
    )
    assert forbidden_download.status_code == 403

    owner_delete_member_file = client.delete(f"/attachments/{attachment_id}", headers=owner)
    assert owner_delete_member_file.status_code == 403

    deleted = client.delete(f"/attachments/{attachment_id}", headers=member)
    assert deleted.status_code == 204
    assert client.get(f"/attachments/{attachment_id}/download", headers=owner).status_code == 404

    second = client.post(
        f"/tasks/{task_id}/attachments",
        files={"file": ("note2.txt", b"second", "text/plain")},
        headers=member,
    )
    assert second.status_code == 201
    admin_delete = client.delete(f"/attachments/{second.json()['id']}", headers=admin)
    assert admin_delete.status_code == 204

    activities = client.get(f"/projects/{project_id}/activities", headers=owner)
    actions = {item["action"] for item in activities.json()["items"]}
    assert "ATTACHMENT_UPLOADED" in actions
    assert "ATTACHMENT_DELETED" in actions


def test_task_crud_access_control(client, setup_users):
    project_id = setup_users["project_id"]
    owner = auth_headers(client, "owner_aca@test.com")
    stranger = auth_headers(client, "stranger_aca@test.com")
    task_id = create_task(client, owner, project_id, "Access task")

    assert client.get(f"/tasks/{task_id}", headers=owner).status_code == 200
    assert client.get(f"/tasks/{task_id}", headers=stranger).status_code == 403
    assert client.put(
        f"/tasks/{task_id}",
        json={"title": "hack"},
        headers=stranger,
    ).status_code == 403
    assert client.patch(
        f"/tasks/{task_id}/status",
        json={"status": "DONE"},
        headers=stranger,
    ).status_code == 403
    assert client.delete(f"/tasks/{task_id}", headers=stranger).status_code == 403
    invalid = client.patch(
        f"/tasks/{task_id}/status",
        json={"status": "WRONG"},
        headers=owner,
    )
    assert invalid.status_code == 400
