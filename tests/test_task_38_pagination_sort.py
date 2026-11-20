"""Bộ test tự động cho Task 38: Implement Pagination & Sort for Tasks."""

import pytest
from fastapi.testclient import TestClient

from app.core.security import hash_password
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.task import Task
from app.models.user import User


@pytest.fixture
def pagination_test_data(db_session):
    """
    Gieo dữ liệu phong phú phục vụ kiểm thử phân trang và sắp xếp:
    Tạo 15 Tasks cho Project 1 và 2 Tasks cho Project 2.
    """
    db = db_session
    # 1. Tạo các User: Owner, Member, Stranger, Assignee 1, Assignee 2
    owner = User(
        email="owner38@test.com",
        full_name="Owner ThirtyEight",
        hashed_password=hash_password("Password123"),
        role="USER",
        is_active=True,
    )
    member = User(
        email="member38@test.com",
        full_name="Member ThirtyEight",
        hashed_password=hash_password("Password123"),
        role="USER",
        is_active=True,
    )
    stranger = User(
        email="stranger38@test.com",
        full_name="Stranger ThirtyEight",
        hashed_password=hash_password("Password123"),
        role="USER",
        is_active=True,
    )
    assignee1 = User(
        email="assignee1@test.com",
        full_name="Assignee One",
        hashed_password=hash_password("Password123"),
        role="USER",
        is_active=True,
    )
    assignee2 = User(
        email="assignee2@test.com",
        full_name="Assignee Two",
        hashed_password=hash_password("Password123"),
        role="USER",
        is_active=True,
    )
    db.add_all([owner, member, stranger, assignee1, assignee2])
    db.commit()
    for u in [owner, member, stranger, assignee1, assignee2]:
        db.refresh(u)

    # 2. Tạo 2 dự án
    project1 = Project(
        name="Project Pagination & Sort Test",
        description="Dự án phục vụ test task 38",
        status="in_progress",
        owner_id=owner.id,
    )
    project2 = Project(
        name="Another Project",
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

    # 4. Tạo 15 Tasks cho Project 1 với các title, status, priority, assignee đa dạng
    # Tiêu đề từ "Task 01" đến "Task 15"
    statuses = ["TODO", "IN_PROGRESS", "DONE"]
    priorities = ["LOW", "MEDIUM", "HIGH"]
    tasks_p1 = []
    for i in range(1, 16):
        title = f"Task {i:02d} - Login module item" if i <= 8 else f"Task {i:02d} - Backend feature"
        t = Task(
            title=title,
            description=f"Description for task {i}",
            status=statuses[(i - 1) % len(statuses)],
            priority=priorities[(i - 1) % len(priorities)],
            project_id=project1.id,
            assignee_id=assignee1.id if i % 2 == 0 else (assignee2.id if i % 3 == 0 else None),
        )
        tasks_p1.append(t)

    # 5. Tạo 2 task cho Project 2
    t_other1 = Task(
        title="Project 2 Task 01",
        description="Thuộc dự án 2",
        status="TODO",
        priority="HIGH",
        project_id=project2.id,
        assignee_id=assignee1.id,
    )
    t_other2 = Task(
        title="Project 2 Task 02",
        description="Thuộc dự án 2",
        status="DONE",
        priority="LOW",
        project_id=project2.id,
        assignee_id=None,
    )

    db.add_all(tasks_p1 + [t_other1, t_other2])
    db.commit()

    return {
        "owner_id": owner.id,
        "member_id": member.id,
        "stranger_id": stranger.id,
        "assignee1_id": assignee1.id,
        "assignee2_id": assignee2.id,
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
# NHÓM 1: KIỂM THỬ PAGINATION
# ==============================================================================

def test_case_01_pagination_defaults(client, pagination_test_data):
    """1. Không truyền page và page_size: mặc định page=1, page_size=10."""
    token = get_token(client, "owner38@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    p_id = pagination_test_data["project1_id"]

    res = client.get(f"/projects/{p_id}/tasks", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["page"] == 1
    assert data["page_size"] == 10
    assert data["total"] == 15
    assert data["total_pages"] == 2
    assert data["has_next"] is True
    assert data["has_previous"] is False
    assert len(data["items"]) == 10


def test_case_02_pagination_page_1(client, pagination_test_data):
    """2. Truyền page = 1, page_size = 5."""
    token = get_token(client, "owner38@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    p_id = pagination_test_data["project1_id"]

    res = client.get(f"/projects/{p_id}/tasks?page=1&page_size=5", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["page"] == 1
    assert data["page_size"] == 5
    assert data["total"] == 15
    assert data["total_pages"] == 3
    assert data["has_next"] is True
    assert data["has_previous"] is False
    assert len(data["items"]) == 5


def test_case_03_pagination_page_2(client, pagination_test_data):
    """3. Truyền page = 2, page_size = 5."""
    token = get_token(client, "owner38@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    p_id = pagination_test_data["project1_id"]

    res = client.get(f"/projects/{p_id}/tasks?page=2&page_size=5", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["page"] == 2
    assert data["page_size"] == 5
    assert data["total"] == 15
    assert data["total_pages"] == 3
    assert data["has_next"] is True
    assert data["has_previous"] is True
    assert len(data["items"]) == 5


def test_case_04_pagination_page_zero(client, pagination_test_data):
    """4. page = 0: phải trả lỗi validation phù hợp (HTTP 400 hoặc 422)."""
    token = get_token(client, "owner38@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    p_id = pagination_test_data["project1_id"]

    res = client.get(f"/projects/{p_id}/tasks?page=0", headers=headers)
    assert res.status_code in (400, 422)


def test_case_05_pagination_page_size_zero(client, pagination_test_data):
    """5. page_size = 0: phải trả lỗi validation phù hợp (HTTP 400 hoặc 422)."""
    token = get_token(client, "owner38@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    p_id = pagination_test_data["project1_id"]

    res = client.get(f"/projects/{p_id}/tasks?page_size=0", headers=headers)
    assert res.status_code in (400, 422)


def test_case_06_pagination_page_size_exceed(client, pagination_test_data):
    """6. page_size vượt giới hạn (ví dụ 101): phải trả lỗi validation phù hợp."""
    token = get_token(client, "owner38@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    p_id = pagination_test_data["project1_id"]

    res = client.get(f"/projects/{p_id}/tasks?page_size=101", headers=headers)
    assert res.status_code in (400, 422)


def test_case_07_pagination_empty_page(client, pagination_test_data):
    """7. Trang không có dữ liệu (page = 99): trả về items rỗng, không gây lỗi 500."""
    token = get_token(client, "owner38@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    p_id = pagination_test_data["project1_id"]

    res = client.get(f"/projects/{p_id}/tasks?page=99&page_size=10", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["page"] == 99
    assert data["total"] == 15
    assert data["total_pages"] == 2
    assert data["has_next"] is False
    assert data["has_previous"] is True
    assert len(data["items"]) == 0


# ==============================================================================
# NHÓM 2: KIỂM THỬ SORT
# ==============================================================================

def test_case_08_sort_created_at_asc(client, pagination_test_data):
    """8. Sắp xếp created_at tăng dần (asc)."""
    token = get_token(client, "owner38@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    p_id = pagination_test_data["project1_id"]

    res = client.get(
        f"/projects/{p_id}/tasks?sort_by=created_at&sort_order=asc&page_size=15",
        headers=headers,
    )
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) == 15
    # ID tăng dần theo thứ tự chèn
    ids = [item["id"] for item in items]
    assert ids == sorted(ids)


def test_case_09_sort_created_at_desc(client, pagination_test_data):
    """9. Sắp xếp created_at giảm dần (desc)."""
    token = get_token(client, "owner38@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    p_id = pagination_test_data["project1_id"]

    res = client.get(
        f"/projects/{p_id}/tasks?sort_by=created_at&sort_order=desc&page_size=15",
        headers=headers,
    )
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) == 15
    ids = [item["id"] for item in items]
    assert ids == sorted(ids, reverse=True)


def test_case_10_sort_by_title(client, pagination_test_data):
    """10. Sắp xếp theo title tăng dần."""
    token = get_token(client, "owner38@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    p_id = pagination_test_data["project1_id"]

    res = client.get(
        f"/projects/{p_id}/tasks?sort_by=title&sort_order=asc&page_size=15",
        headers=headers,
    )
    assert res.status_code == 200
    items = res.json()["items"]
    titles = [item["title"] for item in items]
    assert titles == sorted(titles)


def test_case_11_sort_by_priority(client, pagination_test_data):
    """11. Sắp xếp theo priority."""
    token = get_token(client, "owner38@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    p_id = pagination_test_data["project1_id"]

    res = client.get(
        f"/projects/{p_id}/tasks?sort_by=priority&sort_order=asc&page_size=15",
        headers=headers,
    )
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) == 15


def test_case_12_sort_by_invalid(client, pagination_test_data):
    """12. sort_by không hợp lệ: trả về lỗi validation HTTP 400."""
    token = get_token(client, "owner38@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    p_id = pagination_test_data["project1_id"]

    res = client.get(
        f"/projects/{p_id}/tasks?sort_by=non_existent_field",
        headers=headers,
    )
    assert res.status_code == 400
    assert "Trường sắp xếp 'non_existent_field' không hợp lệ" in res.json()["detail"]


def test_case_13_sort_order_invalid(client, pagination_test_data):
    """13. sort_order không hợp lệ: trả về lỗi validation HTTP 400."""
    token = get_token(client, "owner38@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    p_id = pagination_test_data["project1_id"]

    res = client.get(
        f"/projects/{p_id}/tasks?sort_order=diagonal",
        headers=headers,
    )
    assert res.status_code == 400
    assert "Chiều sắp xếp 'diagonal' không hợp lệ" in res.json()["detail"]


# ==============================================================================
# NHÓM 3: KẾT HỢP SEARCH, FILTER, PAGINATION VÀ SORT
# ==============================================================================

def test_case_14_combine_search_and_pagination(client, pagination_test_data):
    """14. Search + Pagination: tìm 'Login' (8 tasks), trang 1 lấy 3 bản ghi."""
    token = get_token(client, "owner38@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    p_id = pagination_test_data["project1_id"]

    res = client.get(
        f"/projects/{p_id}/tasks?search=Login&page=1&page_size=3",
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 8
    assert data["total_pages"] == 3
    assert data["page"] == 1
    assert data["page_size"] == 3
    assert data["has_next"] is True
    assert len(data["items"]) == 3
    for item in data["items"]:
        assert "login" in item["title"].lower()


def test_case_15_combine_filter_status_and_pagination(client, pagination_test_data):
    """15. Filter status + Pagination: lọc status='IN_PROGRESS' (5 tasks), page=2, page_size=2."""
    token = get_token(client, "owner38@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    p_id = pagination_test_data["project1_id"]

    res = client.get(
        f"/projects/{p_id}/tasks?status=IN_PROGRESS&page=2&page_size=2",
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 5
    assert data["total_pages"] == 3
    assert data["page"] == 2
    assert len(data["items"]) == 2
    for item in data["items"]:
        assert item["status"] == "IN_PROGRESS"


def test_case_16_combine_filter_priority_and_sort(client, pagination_test_data):
    """16. Filter priority + Sort: lọc priority='HIGH' và sort theo title asc."""
    token = get_token(client, "owner38@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    p_id = pagination_test_data["project1_id"]

    res = client.get(
        f"/projects/{p_id}/tasks?priority=HIGH&sort_by=title&sort_order=asc&page_size=20",
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 5
    items = data["items"]
    assert len(items) == 5
    for item in items:
        assert item["priority"] == "HIGH"
    titles = [item["title"] for item in items]
    assert titles == sorted(titles)


def test_case_17_combine_filter_assignee_and_sort(client, pagination_test_data):
    """17. Filter assignee + Sort: lọc theo assignee1 và sort created_at desc."""
    token = get_token(client, "owner38@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    p_id = pagination_test_data["project1_id"]
    a1_id = pagination_test_data["assignee1_id"]

    res = client.get(
        f"/projects/{p_id}/tasks?assignee_id={a1_id}&sort_by=created_at&sort_order=desc",
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()
    for item in data["items"]:
        assert item["assignee_id"] == a1_id


def test_case_18_combine_search_filter_and_pagination(client, pagination_test_data):
    """18. Search + Filter + Pagination: search='Login', status='TODO', page=1, page_size=2."""
    token = get_token(client, "owner38@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    p_id = pagination_test_data["project1_id"]

    res = client.get(
        f"/projects/{p_id}/tasks?search=Login&status=TODO&page=1&page_size=2",
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 3
    assert data["total_pages"] == 2
    assert len(data["items"]) == 2
    for item in data["items"]:
        assert "login" in item["title"].lower()
        assert item["status"] == "TODO"


def test_case_19_combine_all_four_features(client, pagination_test_data):
    """19. Search + Filter + Sort + Pagination: kết hợp đồng thời toàn bộ tiêu chí."""
    token = get_token(client, "owner38@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    p_id = pagination_test_data["project1_id"]
    a1_id = pagination_test_data["assignee1_id"]

    res = client.get(
        f"/projects/{p_id}/tasks?search=Login&status=TODO&assignee_id={a1_id}&sort_by=title&sort_order=desc&page=1&page_size=5",
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert data["page"] == 1
    assert data["page_size"] == 5
    for item in data["items"]:
        assert "login" in item["title"].lower()
        assert item["status"] == "TODO"
        assert item["assignee_id"] == a1_id


def test_case_20_no_results_after_filtering(client, pagination_test_data):
    """20. Không có kết quả sau khi lọc: total=0, items=[], total_pages=0, has_next=False."""
    token = get_token(client, "owner38@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    p_id = pagination_test_data["project1_id"]

    res = client.get(
        f"/projects/{p_id}/tasks?search=KhongTheTonTaiDauNhe",
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 0
    assert data["total_pages"] == 0
    assert data["has_next"] is False
    assert data["has_previous"] is False
    assert len(data["items"]) == 0


# ==============================================================================
# NHÓM 4: KIỂM TRA QUYỀN TRUY CẬP VÀ CÁCH LY DỰ ÁN
# ==============================================================================

def test_case_21_stranger_forbidden(client, pagination_test_data):
    """21. User không thuộc Project không được truy cập: trả về HTTP 403 Forbidden."""
    token = get_token(client, "stranger38@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    p1_id = pagination_test_data["project1_id"]

    res = client.get(f"/projects/{p1_id}/tasks", headers=headers)
    assert res.status_code == 403
    assert "Bạn không có quyền truy cập" in res.json()["detail"]


def test_case_22_isolate_tasks_across_projects(client, pagination_test_data):
    """22. Không thể lấy Task của Project khác: chỉ trả về task thuộc đúng project_id."""
    token = get_token(client, "stranger38@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    p2_id = pagination_test_data["project2_id"]

    res = client.get(f"/projects/{p2_id}/tasks", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 2
    for item in data["items"]:
        assert item["project_id"] == p2_id
