import os
import sys

# Thêm thư mục gốc vào sys.path để import được app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.main import app
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.user import User
from tests.conftest import TestingSessionLocal


def create_test_token(email: str, role: str = "USER") -> str:
    """Lấy user_id từ DB test và tạo JWT access token chuẩn của dự án."""
    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        subject = user.id if user else 999999
        user_role = user.role if user else role
        return create_access_token(subject=subject, role=user_role)
    finally:
        db.close()


@pytest.fixture
def seed_project_data():
    """Chèn dữ liệu mẫu vào DB chung của test suite cho các test trong file này."""
    db = TestingSessionLocal()
    try:
        user1 = User(
            email="owner@test.com",
            full_name="Project Owner",
            hashed_password="hashed_pwd",
            role="USER",
            is_active=True,
        )
        user2 = User(
            email="member@test.com",
            full_name="Project Member",
            hashed_password="hashed_pwd",
            role="USER",
            is_active=True,
        )
        outsider = User(
            email="outsider@test.com",
            full_name="Outsider User",
            hashed_password="hashed_pwd",
            role="USER",
            is_active=True,
        )
        inactive_user = User(
            email="inactive@test.com",
            full_name="Inactive User",
            hashed_password="hashed_pwd",
            role="USER",
            is_active=False,
        )

        db.add_all([user1, user2, outsider, inactive_user])
        db.commit()

        proj1 = Project(
            name="AI Interview System",
            description="Core backend for AI Interview",
            owner_id=user1.id,
        )
        db.add(proj1)
        db.commit()

        pm = ProjectMember(
            project_id=proj1.id,
            user_id=user2.id,
            role="MEMBER",
        )
        db.add(pm)
        db.commit()
    finally:
        db.close()


pytestmark = pytest.mark.usefixtures("seed_project_data")
client = TestClient(app)


def test_get_project_detail_unauthenticated():
    """1. Gọi endpoint khi chưa đăng nhập (không có token) -> Phải trả về 401 Unauthorized."""
    response = client.get("/projects/1")
    assert response.status_code == 401


def test_get_project_detail_by_owner():
    """2. Chủ sở hữu dự án (Owner) xem chi tiết -> Phải trả về 200 OK với thông tin dự án."""
    token = create_test_token("owner@test.com")
    response = client.get(
        "/projects/1",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["name"] == "AI Interview System"
    assert data["owner_id"] is not None


def test_get_project_detail_by_member_forbidden():
    """3. Thành viên thường (không phải owner/admin/manager) gọi GET /projects/1 -> 403 Forbidden."""
    token = create_test_token("member@test.com")
    response = client.get(
        "/projects/1",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


def test_get_project_detail_by_non_member():
    """4. Người dùng không thuộc dự án truy cập -> Phải trả về 403 Forbidden."""
    token = create_test_token("outsider@test.com")
    response = client.get(
        "/projects/1",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
    assert "không có quyền" in response.json()["detail"].lower()


def test_get_project_detail_not_found():
    """5. Dự án không tồn tại -> Phải trả về 404 Not Found."""
    token = create_test_token("owner@test.com")
    response = client.get(
        "/projects/9999",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404
    assert "không tìm thấy" in response.json()["detail"].lower()


def test_get_project_detail_inactive_user():
    """6. Người dùng bị vô hiệu hóa truy cập -> Phải trả về 403 Forbidden."""
    token = create_test_token("inactive@test.com")
    response = client.get(
        "/projects/1",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


# ==========================================
# TESTS CHO TASK TB8ED6A: POST /projects
# ==========================================


def test_create_project_success():
    """7. Người dùng đăng nhập tạo dự án thành công -> Trả về 201 và gán đúng owner_id."""
    token = create_test_token("outsider@test.com")
    payload = {
        "name": "Dự án mới tạo",
        "description": "Mô tả dự án mới",
    }
    response = client.post(
        "/projects",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Dự án mới tạo"
    assert data["description"] == "Mô tả dự án mới"
    assert "id" in data
    new_project_id = data["id"]

    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.email == "outsider@test.com").first()
        assert user is not None
        assert data["owner_id"] == user.id

        project = db.query(Project).filter(Project.id == new_project_id).first()
        assert project is not None
        assert project.owner_id == user.id
    finally:
        db.close()


def test_create_project_unauthenticated():
    """8. Tạo dự án khi chưa đăng nhập -> Phải trả về 401 Unauthorized."""
    response = client.post(
        "/projects",
        json={"name": "Dự án không có quyền", "description": "Test unauth"},
    )
    assert response.status_code == 401


def test_create_project_inactive_user():
    """9. Tài khoản bị vô hiệu hóa tạo dự án -> Phải trả về 403 Forbidden."""
    token = create_test_token("inactive@test.com")
    response = client.post(
        "/projects",
        json={"name": "Dự án từ user bị khóa", "description": "Test inactive"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


def test_create_project_validation_error():
    """10. Gửi thiếu trường bắt buộc 'name' -> Phải trả về 422 Unprocessable Entity."""
    token = create_test_token("owner@test.com")
    response = client.post(
        "/projects",
        json={"description": "Thiếu tên dự án"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 422


def test_created_project_owner_can_read_detail():
    """11. Người tạo dự án xem được chi tiết dự án vừa tạo."""
    token = create_test_token("outsider@test.com")
    create_res = client.post(
        "/projects",
        json={"name": "Dự án xem chi tiết", "description": "Test read detail"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create_res.status_code == 201
    proj_id = create_res.json()["id"]

    detail_res = client.get(
        f"/projects/{proj_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    assert detail_data["id"] == proj_id
    assert detail_data["name"] == "Dự án xem chi tiết"


# ==========================================
# TESTS CHO TASK TB8ED82: GET /projects/{id}/members
# ==========================================


def test_get_project_members_by_member():
    """12. Thành viên hoặc chủ dự án xem danh sách thành viên -> Trả về 200 OK."""
    token = create_test_token("member@test.com")
    response = client.get(
        "/projects/1/members",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    members = response.json()
    assert isinstance(members, list)
    assert len(members) >= 1
    emails = [m["email"] for m in members]
    assert "member@test.com" in emails


def test_get_project_members_forbidden_outsider():
    """13. Người ngoài dự án gọi GET /projects/1/members -> Trả về 403 Forbidden."""
    token = create_test_token("outsider@test.com")
    response = client.get(
        "/projects/1/members",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


def test_get_project_members_not_found():
    """14. Dự án không tồn tại -> Trả về 404 Not Found."""
    token = create_test_token("owner@test.com")
    response = client.get(
        "/projects/9999/members",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


    # ==========================================
# TESTS CHO TASK TB8ED76: VALIDATION & 404 PROJECT/USER
# ==========================================


def test_create_project_blank_or_too_long_name():
    """15. Tên project chỉ chứa khoảng trắng hoặc vượt 255 ký tự -> Trả về 422."""
    token = create_test_token("owner@test.com")

    # Tên toàn khoảng trắng
    res_blank = client.post(
        "/projects",
        json={"name": "     ", "description": "Tên toàn dấu cách"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_blank.status_code == 422

    # Tên vượt quá 255 ký tự
    res_long = client.post(
        "/projects",
        json={"name": "A" * 256, "description": "Tên quá dài"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_long.status_code == 422


def test_update_project_blank_name_and_not_found():
    """16. Cập nhật project không tồn tại (404) hoặc tên trống (422)."""
    token = create_test_token("owner@test.com")

    res_not_found = client.put(
        "/projects/9999",
        json={"name": "Tên hợp lệ"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_not_found.status_code == 404

    res_blank = client.put(
        "/projects/1",
        json={"name": "   "},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_blank.status_code == 422


def test_add_member_nonexistent_project_or_user():
    """17. Thêm member vào project không tồn tại hoặc user_id không tồn tại -> Trả về 404."""
    token = create_test_token("owner@test.com")

    # Project không tồn tại
    res_no_proj = client.post(
        "/projects/9999/members",
        json={"user_id": 2, "role": "MEMBER"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_no_proj.status_code == 404

    # User không tồn tại
    res_no_user = client.post(
        "/projects/1/members",
        json={"user_id": 99999, "role": "MEMBER"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_no_user.status_code == 404



# ==========================================
# TESTS CHO TASK TB8ED79: SOFT DELETE PROJECT
# ==========================================


def test_soft_delete_project_preserves_data_in_db():
    """18. Xóa mềm project (204): ẩn khỏi API (404/list) nhưng bản ghi vẫn còn trong DB với is_deleted=True & deleted_at."""
    token = create_test_token("owner@test.com")

    # Gọi DELETE /projects/1
    del_res = client.delete(
        "/projects/1",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert del_res.status_code == 204

    # 1. Gọi GET /projects/1 sau khi xóa -> Trả về 404 Not Found
    get_res = client.get(
        "/projects/1",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_res.status_code == 404

    # 2. Gọi GET /projects -> Không còn xuất hiện trong danh sách
    list_res = client.get(
        "/projects",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert list_res.status_code == 200
    assert all(p["id"] != 1 for p in list_res.json())

    # 3. Kiểm tra trực tiếp trong Database: bản ghi vẫn tồn tại, is_deleted=True, deleted_at != None
    db = TestingSessionLocal()
    try:
        project_in_db = db.query(Project).filter(Project.id == 1).first()
        assert project_in_db is not None
        assert project_in_db.is_deleted is True
        assert project_in_db.deleted_at is not None
    finally:
        db.close()


def test_soft_delete_project_forbidden_non_owner():
    """19. Người không phải chủ dự án gọi DELETE /projects/1 -> Trả về 403 Forbidden."""
    token = create_test_token("member@test.com")
    res = client.delete(
        "/projects/1",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403