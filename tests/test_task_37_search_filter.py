"""Bộ test tự động cho Task 37: Implement Search & Filter for Tasks."""

import pytest
from fastapi.testclient import TestClient

from app.core.security import hash_password
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.task import Task
from app.models.user import User


@pytest.fixture
def test_data(db_session):
    """Gieo dữ liệu mẫu phục vụ kiểm thử Search & Filter Tasks."""
    db = db_session
    # 1. Tạo các User: Owner, Member, Stranger, Assignee
    owner = User(
        email="owner@test.com",
        full_name="Project Owner",
        hashed_password=hash_password("Password123"),
        role="USER",
        is_active=True,
    )
    member = User(
        email="member@test.com",
        full_name="Project Member",
        hashed_password=hash_password("Password123"),
        role="USER",
        is_active=True,
    )
    stranger = User(
        email="stranger@test.com",
        full_name="Stranger User",
        hashed_password=hash_password("Password123"),
        role="USER",
        is_active=True,
    )
    assignee_user = User(
        email="assignee@test.com",
        full_name="Assignee User",
        hashed_password=hash_password("Password123"),
        role="USER",
        is_active=True,
    )
    admin = User(
        email="admin_sys@test.com",
        full_name="System Admin",
        hashed_password=hash_password("Password123"),
        role="ADMIN",
        is_active=True,
    )
    db.add_all([owner, member, stranger, assignee_user, admin])
    db.commit()
    for u in [owner, member, stranger, assignee_user, admin]:
        db.refresh(u)

    # 2. Tạo 2 Project: Project 1 (chính) và Project 2 (dự án khác)
    project1 = Project(
        name="AI Interview Core Project",
        description="Dự án chính để test",
        status="in_progress",
        owner_id=owner.id,
    )
    project2 = Project(
        name="Another Unrelated Project",
        description="Dự án khác để test cách ly",
        status="in_progress",
        owner_id=stranger.id,
    )
    db.add_all([project1, project2])
    db.commit()
    db.refresh(project1)
    db.refresh(project2)

    # 3. Gán member vào Project 1
    pm = ProjectMember(project_id=project1.id, user_id=member.id, role="MEMBER")
    db.add(pm)
    db.commit()

    # 4. Tạo các Task cho Project 1
    t1 = Task(
        title="Implement user login flow",
        description="Xử lý đăng nhập với JWT",
        status="IN_PROGRESS",
        priority="HIGH",
        project_id=project1.id,
        assignee_id=assignee_user.id,
    )
    t2 = Task(
        title="Design Login UI mockup",
        description="Thiết kế giao diện đăng nhập",
        status="DONE",
        priority="LOW",
        project_id=project1.id,
        assignee_id=member.id,
    )
    t3 = Task(
        title="Fix login security bugs",
        description="Kiểm tra lỗ hổng bảo mật",
        status="TODO",
        priority="HIGH",
        project_id=project1.id,
        assignee_id=None,  # Chưa giao cho ai
    )
    t4 = Task(
        title="Setup database migrations",
        description="Alembic config",
        status="DONE",
        priority="MEDIUM",
        project_id=project1.id,
        assignee_id=assignee_user.id,
    )

    # 5. Tạo Task cho Project 2 (có chứa từ login để test không lẫn sang project 1)
    t_other = Task(
        title="Project 2 Login Service",
        description="Thuộc dự án 2",
        status="IN_PROGRESS",
        priority="HIGH",
        project_id=project2.id,
        assignee_id=assignee_user.id,
    )
    db.add_all([t1, t2, t3, t4, t_other])
    db.commit()

    return {
        "owner_id": owner.id,
        "member_id": member.id,
        "stranger_id": stranger.id,
        "assignee_id": assignee_user.id,
        "admin_id": admin.id,
        "project1_id": project1.id,
        "project2_id": project2.id,
    }


def get_token(client: TestClient, email: str) -> str:
    res = client.post(
        "/auth/login-json",
        json={"email": email, "password": "Password123"},
    )
    return res.json()["access_token"]


# ==============================================================================
# Case 1: Gọi API không có query parameter: trả danh sách Task bình thường
# ==============================================================================
def test_case_01_no_query_param(client, test_data):
    token = get_token(client, "owner@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    p_id = test_data["project1_id"]

    res = client.get(f"/projects/{p_id}/tasks", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 4
    for task in data:
        assert task["project_id"] == p_id


# ==============================================================================
# Case 2: Search theo title có kết quả
# ==============================================================================
def test_case_02_search_title_found(client, test_data):
    token = get_token(client, "owner@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    p_id = test_data["project1_id"]

    res = client.get(f"/projects/{p_id}/tasks?search=mockup", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert "Design Login UI mockup" in data[0]["title"]


# ==============================================================================
# Case 3: Search theo title không có kết quả
# ==============================================================================
def test_case_03_search_title_not_found(client, test_data):
    token = get_token(client, "owner@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    p_id = test_data["project1_id"]

    res = client.get(
        f"/projects/{p_id}/tasks?search=NonExistentTaskTitle", headers=headers
    )
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 0


# ==============================================================================
# Case 4: Search với chữ hoa và chữ thường (case-insensitive)
# ==============================================================================
def test_case_04_search_case_insensitive(client, test_data):
    token = get_token(client, "owner@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    p_id = test_data["project1_id"]

    # Search bằng chữ thường "login"
    res_lower = client.get(f"/projects/{p_id}/tasks?search=login", headers=headers)
    assert res_lower.status_code == 200
    # Search bằng chữ hoa "LOGIN"
    res_upper = client.get(f"/projects/{p_id}/tasks?search=LOGIN", headers=headers)
    assert res_upper.status_code == 200

    # Cả hai đều tìm được 3 task chứa từ "login"/"Login"
    assert len(res_lower.json()) == 3
    assert len(res_upper.json()) == 3


# ==============================================================================
# Case 5: Filter status = TODO
# ==============================================================================
def test_case_05_filter_status_todo(client, test_data):
    token = get_token(client, "owner@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    p_id = test_data["project1_id"]

    res = client.get(f"/projects/{p_id}/tasks?status=TODO", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["status"] == "TODO"


# ==============================================================================
# Case 6: Filter status = IN_PROGRESS
# ==============================================================================
def test_case_06_filter_status_in_progress(client, test_data):
    token = get_token(client, "owner@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    p_id = test_data["project1_id"]

    res = client.get(
        f"/projects/{p_id}/tasks?status=IN_PROGRESS", headers=headers
    )
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["status"] == "IN_PROGRESS"


# ==============================================================================
# Case 7: Filter status không hợp lệ -> 400 Bad Request, không gây lỗi 500
# ==============================================================================
def test_case_07_filter_status_invalid(client, test_data):
    token = get_token(client, "owner@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    p_id = test_data["project1_id"]

    res = client.get(f"/projects/{p_id}/tasks?status=INVALID_STATUS", headers=headers)
    assert res.status_code == 400
    assert "Trạng thái 'INVALID_STATUS' không hợp lệ" in res.json()["detail"]


# ==============================================================================
# Case 8: Filter priority = HIGH
# ==============================================================================
def test_case_08_filter_priority_high(client, test_data):
    token = get_token(client, "owner@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    p_id = test_data["project1_id"]

    res = client.get(f"/projects/{p_id}/tasks?priority=HIGH", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 2
    for t in data:
        assert t["priority"] == "HIGH"


# ==============================================================================
# Case 9: Filter priority không hợp lệ -> 400 Bad Request
# ==============================================================================
def test_case_09_filter_priority_invalid(client, test_data):
    token = get_token(client, "owner@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    p_id = test_data["project1_id"]

    res = client.get(
        f"/projects/{p_id}/tasks?priority=SUPER_HIGH", headers=headers
    )
    assert res.status_code == 400
    assert "Mức độ ưu tiên 'SUPER_HIGH' không hợp lệ" in res.json()["detail"]


# ==============================================================================
# Case 10: Filter theo assignee_id có kết quả
# ==============================================================================
def test_case_10_filter_assignee_found(client, test_data):
    token = get_token(client, "owner@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    p_id = test_data["project1_id"]
    assignee_id = test_data["assignee_id"]

    res = client.get(
        f"/projects/{p_id}/tasks?assignee_id={assignee_id}", headers=headers
    )
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 2
    for t in data:
        assert t["assignee_id"] == assignee_id


# ==============================================================================
# Case 11: Filter theo assignee_id không có kết quả
# ==============================================================================
def test_case_11_filter_assignee_not_found(client, test_data):
    token = get_token(client, "owner@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    p_id = test_data["project1_id"]

    # ID 99999 không được gán task nào
    res = client.get(f"/projects/{p_id}/tasks?assignee_id=99999", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 0


# ==============================================================================
# Case 12: Kết hợp search + status
# ==============================================================================
def test_case_12_combine_search_and_status(client, test_data):
    token = get_token(client, "owner@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    p_id = test_data["project1_id"]

    # Search 'login' + status 'DONE'
    res = client.get(
        f"/projects/{p_id}/tasks?search=login&status=DONE", headers=headers
    )
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["title"] == "Design Login UI mockup"
    assert data[0]["status"] == "DONE"


# ==============================================================================
# Case 13: Kết hợp status + priority
# ==============================================================================
def test_case_13_combine_status_and_priority(client, test_data):
    token = get_token(client, "owner@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    p_id = test_data["project1_id"]

    res = client.get(
        f"/projects/{p_id}/tasks?status=DONE&priority=MEDIUM", headers=headers
    )
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["title"] == "Setup database migrations"
    assert data[0]["status"] == "DONE"
    assert data[0]["priority"] == "MEDIUM"


# ==============================================================================
# Case 14: Kết hợp search + status + priority + assignee_id
# ==============================================================================
def test_case_14_combine_all_four_filters(client, test_data):
    token = get_token(client, "owner@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    p_id = test_data["project1_id"]
    assignee_id = test_data["assignee_id"]

    res = client.get(
        f"/projects/{p_id}/tasks?search=login&status=IN_PROGRESS&priority=HIGH&assignee_id={assignee_id}",
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    task = data[0]
    assert "login" in task["title"].lower()
    assert task["status"] == "IN_PROGRESS"
    assert task["priority"] == "HIGH"
    assert task["assignee_id"] == assignee_id


# ==============================================================================
# Case 15: Người không thuộc Project gọi API phải bị từ chối 403 Forbidden
# ==============================================================================
def test_case_15_stranger_forbidden(client, test_data):
    token = get_token(client, "stranger@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    p_id = test_data["project1_id"]

    res = client.get(f"/projects/{p_id}/tasks", headers=headers)
    assert res.status_code == 403
    assert "Bạn không có quyền truy cập" in res.json()["detail"]


# ==============================================================================
# Case 16: Không thể lấy Task từ Project khác bằng cách thay đổi project_id
# ==============================================================================
def test_case_16_isolate_tasks_across_projects(client, test_data):
    # Stranger là owner của Project 2, gọi Project 2 tìm 'login'
    token = get_token(client, "stranger@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    p2_id = test_data["project2_id"]

    res = client.get(f"/projects/{p2_id}/tasks?search=login", headers=headers)
    assert res.status_code == 200
    data = res.json()
    # Chỉ trả về task của project 2, KHÔNG được chứa task của project 1
    assert len(data) == 1
    assert data[0]["title"] == "Project 2 Login Service"
    assert data[0]["project_id"] == p2_id


# ==============================================================================
# Case Bonus: Thành viên dự án (Member) và Admin truy cập hợp lệ
# ==============================================================================
def test_case_member_and_admin_access(client, test_data):
    p_id = test_data["project1_id"]

    # 1. Member trong project_members
    member_token = get_token(client, "member@test.com")
    res_mem = client.get(
        f"/projects/{p_id}/tasks",
        headers={"Authorization": f"Bearer {member_token}"},
    )
    assert res_mem.status_code == 200
    assert len(res_mem.json()) == 4

    # 2. System Admin
    admin_token = get_token(client, "admin_sys@test.com")
    res_admin = client.get(
        f"/projects/{p_id}/tasks",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_admin.status_code == 200
    assert len(res_admin.json()) == 4


# ==============================================================================
# Case Bonus: Dự án không tồn tại -> 404 Not Found
# ==============================================================================
def test_case_project_not_found(client, test_data):
    token = get_token(client, "owner@test.com")
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/projects/999999/tasks", headers=headers)
    assert res.status_code == 404
    assert "Không tìm thấy dự án" in res.json()["detail"]
