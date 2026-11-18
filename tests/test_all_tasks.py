"""Bộ test tự động kiểm thử đầy đủ 11 nhiệm vụ của dự án."""

import pytest
from app.core.security import hash_password, validate_password_strength, verify_password


# ==============================================================================
# Task 5: Authentication – Password (2 điểm Chính)
# ==============================================================================
def test_task_05_password_hashing_and_validation():
    plain = "MySecretPassword@123"
    hashed = hash_password(plain)

    # 1. Mật khẩu không được lưu dạng rõ
    assert hashed != plain
    # 2. Verify mật khẩu đúng
    assert verify_password(plain, hashed) is True
    # 3. Verify mật khẩu sai
    assert verify_password("WrongPassword", hashed) is False

    # 4. Kiểm tra độ mạnh mật khẩu (yêu cầu >= 6 ký tự)
    valid, _ = validate_password_strength("123456")
    assert valid is True
    invalid, msg = validate_password_strength("12345")
    assert invalid is False
    assert "ít nhất 6 ký tự" in msg


# ==============================================================================
# Task 9: Authentication – Register (3 điểm Chính)
# ==============================================================================
def test_task_09_register_success_and_duplicate(client):
    # Đăng ký thành công
    payload = {
        "email": "user1@example.com",
        "full_name": "Nguyen Van A",
        "password": "Password@123",
        "role": "user",
    }
    res = client.post("/auth/register", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["email"] == "user1@example.com"
    assert data["full_name"] == "Nguyen Van A"
    assert data["role"] == "user"
    assert "hashed_password" not in data

    # Đăng ký trùng email -> 400 Bad Request
    res_dup = client.post("/auth/register", json=payload)
    assert res_dup.status_code == 400
    assert "đã được đăng ký" in res_dup.json()["detail"]


# ==============================================================================
# Task 6: Authentication – Login (3 điểm Chính)
# ==============================================================================
def test_task_06_login_success_and_failure(client):
    # Đăng ký trước
    client.post(
        "/auth/register",
        json={
            "email": "login_user@example.com",
            "full_name": "Login Tester",
            "password": "Password123",
        },
    )

    # 1. Đăng nhập thành công qua form data (OAuth2 standard)
    res = client.post(
        "/auth/login",
        data={"username": "login_user@example.com", "password": "Password123"},
    )
    assert res.status_code == 200
    tokens = res.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["token_type"] == "bearer"

    # 2. Đăng nhập qua JSON body
    res_json = client.post(
        "/auth/login-json",
        json={"email": "login_user@example.com", "password": "Password123"},
    )
    assert res_json.status_code == 200
    assert "access_token" in res_json.json()

    # 3. Đăng nhập sai mật khẩu -> 401
    res_wrong = client.post(
        "/auth/login-json",
        json={"email": "login_user@example.com", "password": "WrongPassword"},
    )
    assert res_wrong.status_code == 401


# ==============================================================================
# Task 10: Refresh token (2 điểm Bonus)
# ==============================================================================
def test_task_10_refresh_token(client):
    client.post(
        "/auth/register",
        json={
            "email": "refresh_user@example.com",
            "full_name": "Refresh Tester",
            "password": "Password123",
        },
    )
    login_res = client.post(
        "/auth/login-json",
        json={"email": "refresh_user@example.com", "password": "Password123"},
    )
    refresh_token = login_res.json()["refresh_token"]

    # Làm mới token
    res = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert res.status_code == 200
    new_tokens = res.json()
    assert "access_token" in new_tokens
    assert "refresh_token" in new_tokens

    # Gửi refresh token giả mạo -> 401
    res_invalid = client.post(
        "/auth/refresh", json={"refresh_token": "invalid.jwt.token"}
    )
    assert res_invalid.status_code == 401


# ==============================================================================
# Task 11: Authentication – Current user (3 điểm Chính)
# ==============================================================================
def test_task_11_current_user(client):
    client.post(
        "/auth/register",
        json={
            "email": "current_user@example.com",
            "full_name": "Current Tester",
            "password": "Password123",
        },
    )
    login_res = client.post(
        "/auth/login-json",
        json={"email": "current_user@example.com", "password": "Password123"},
    )
    access_token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # Lấy thông tin user hiện tại
    res = client.get("/auth/me", headers=headers)
    assert res.status_code == 200
    user_info = res.json()
    assert user_info["email"] == "current_user@example.com"
    assert user_info["full_name"] == "Current Tester"

    # Không truyền token -> 401
    res_no_auth = client.get("/auth/me")
    assert res_no_auth.status_code == 401


# ==============================================================================
# Task 4: User – Profile (2 điểm Chính)
# ==============================================================================
def test_task_04_user_profile(client):
    client.post(
        "/auth/register",
        json={
            "email": "profile_user@example.com",
            "full_name": "Profile Name",
            "password": "Password123",
        },
    )
    login_res = client.post(
        "/auth/login-json",
        json={"email": "profile_user@example.com", "password": "Password123"},
    )
    headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    # 1. Xem profile
    res_profile = client.get("/users/profile", headers=headers)
    assert res_profile.status_code == 200
    assert res_profile.json()["full_name"] == "Profile Name"

    # 2. Cập nhật profile
    res_update = client.put(
        "/users/profile",
        json={"full_name": "Profile Updated Name"},
        headers=headers,
    )
    assert res_update.status_code == 200
    assert res_update.json()["full_name"] == "Profile Updated Name"


# ==============================================================================
# Task 7: Authorization – Role guard (3 điểm Chính) & Task 8: Danh sách user (3 điểm Chính)
# ==============================================================================
def test_task_07_role_guard_and_task_08_list_users(client):
    # Tạo 1 admin và 1 user thường
    client.post(
        "/auth/register",
        json={
            "email": "admin_role@example.com",
            "full_name": "Admin Tester",
            "password": "Password123",
            "role": "admin",
        },
    )
    client.post(
        "/auth/register",
        json={
            "email": "regular_user@example.com",
            "full_name": "Regular Tester",
            "password": "Password123",
            "role": "user",
        },
    )

    admin_login = client.post(
        "/auth/login-json",
        json={"email": "admin_role@example.com", "password": "Password123"},
    )
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

    user_login = client.post(
        "/auth/login-json",
        json={"email": "regular_user@example.com", "password": "Password123"},
    )
    user_headers = {"Authorization": f"Bearer {user_login.json()['access_token']}"}

    # User thường gọi endpoint GET /users -> 403 Forbidden (Role guard)
    res_forbidden = client.get("/users", headers=user_headers)
    assert res_forbidden.status_code == 403
    assert "Bạn không có quyền" in res_forbidden.json()["detail"]

    # Admin gọi endpoint GET /users -> 200 OK (Task 8: Danh sách user)
    res_admin = client.get("/users", headers=admin_headers)
    assert res_admin.status_code == 200
    users_list = res_admin.json()
    assert len(users_list) >= 2


# ==============================================================================
# Task 3: User – Đổi mật khẩu (3 điểm Bonus)
# ==============================================================================
def test_task_03_change_password(client):
    client.post(
        "/auth/register",
        json={
            "email": "change_pwd@example.com",
            "full_name": "Change Pwd",
            "password": "OldPassword123",
        },
    )
    login_res = client.post(
        "/auth/login-json",
        json={"email": "change_pwd@example.com", "password": "OldPassword123"},
    )
    headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    # Đổi mật khẩu thành công
    change_res = client.post(
        "/auth/change-password",
        json={
            "old_password": "OldPassword123",
            "new_password": "NewPassword456",
        },
        headers=headers,
    )
    assert change_res.status_code == 200

    # Đăng nhập bằng mật khẩu cũ -> thất bại
    old_login = client.post(
        "/auth/login-json",
        json={"email": "change_pwd@example.com", "password": "OldPassword123"},
    )
    assert old_login.status_code == 401

    # Đăng nhập bằng mật khẩu mới -> thành công
    new_login = client.post(
        "/auth/login-json",
        json={"email": "change_pwd@example.com", "password": "NewPassword456"},
    )
    assert new_login.status_code == 200


# ==============================================================================
# Task 2: User – Quên/Reset mật khẩu (5 điểm Bonus)
# ==============================================================================
def test_task_02_forgot_and_reset_password(client):
    client.post(
        "/auth/register",
        json={
            "email": "forgot_user@example.com",
            "full_name": "Forgot Tester",
            "password": "InitialPassword123",
        },
    )

    # 1. Yêu cầu mã đặt lại mật khẩu
    forgot_res = client.post(
        "/auth/forgot-password",
        json={"email": "forgot_user@example.com"},
    )
    assert forgot_res.status_code == 200
    reset_token = forgot_res.json()["reset_token"]
    assert reset_token is not None

    # 2. Đặt lại mật khẩu với reset token
    reset_res = client.post(
        "/auth/reset-password",
        json={
            "token": reset_token,
            "new_password": "BrandNewPassword789",
        },
    )
    assert reset_res.status_code == 200

    # 3. Đăng nhập bằng mật khẩu mới
    login_res = client.post(
        "/auth/login-json",
        json={"email": "forgot_user@example.com", "password": "BrandNewPassword789"},
    )
    assert login_res.status_code == 200


# ==============================================================================
# Task 1: Project – Danh sách dự án (3 điểm Chính)
# ==============================================================================
def test_task_01_project_management(client):
    # Đăng ký user
    client.post(
        "/auth/register",
        json={
            "email": "project_owner@example.com",
            "full_name": "Project Owner",
            "password": "Password123",
        },
    )
    login_res = client.post(
        "/auth/login-json",
        json={"email": "project_owner@example.com", "password": "Password123"},
    )
    headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    # 1. Tạo dự án mới
    create_res = client.post(
        "/projects",
        json={
            "name": "Dự án Website Thương mại Điện tử",
            "description": "Xây dựng website bán hàng trực tuyến",
            "status": "in_progress",
        },
        headers=headers,
    )
    assert create_res.status_code == 201
    project_id = create_res.json()["id"]

    # 2. Lấy danh sách dự án (Task 1)
    list_res = client.get("/projects", headers=headers)
    assert list_res.status_code == 200
    projects = list_res.json()
    assert len(projects) >= 1
    assert projects[0]["name"] == "Dự án Website Thương mại Điện tử"

    # 3. Tìm kiếm dự án theo tên và lọc theo trạng thái
    search_res = client.get("/projects?search=Website&status=in_progress", headers=headers)
    assert search_res.status_code == 200
    assert len(search_res.json()) >= 1

    # 4. Xem chi tiết dự án
    detail_res = client.get(f"/projects/{project_id}", headers=headers)
    assert detail_res.status_code == 200
    assert detail_res.json()["id"] == project_id
