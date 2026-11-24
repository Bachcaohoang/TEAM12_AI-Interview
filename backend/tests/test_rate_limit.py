"""Kiểm thử tính năng Rate Limiting và Anti Brute-Force cho Auth (Task TB8ED5B)."""

import os
import sys

# Thêm thư mục gốc vào sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest


# ==============================================================================
# 1. Rate Limit trên /auth/register (Tối đa 3 requests/phút từ 1 IP)
# ==============================================================================
def test_register_rate_limit(client):
    """
    Gửi 3 request đăng ký liên tiếp -> Thành công (201).
    Gửi request thứ 4 từ cùng IP -> Bị chặn với HTTP 429 Too Many Requests và có header Retry-After.
    """
    for i in range(1, 4):
        res = client.post(
            "/auth/register",
            json={
                "email": f"rate_user_{i}@example.com",
                "full_name": f"Rate User {i}",
                "password": "Password123",
            },
        )
        assert res.status_code == 201, f"Request {i} thất bại: {res.text}"

    # Request thứ 4 từ cùng IP -> Phải bị chặn với 429
    res_blocked = client.post(
        "/auth/register",
        json={
            "email": "rate_user_4@example.com",
            "full_name": "Rate User 4",
            "password": "Password123",
        },
    )
    assert res_blocked.status_code == 429
    assert "quá nhiều yêu cầu" in res_blocked.json()["detail"].lower()
    assert "Retry-After" in res_blocked.headers
    assert int(res_blocked.headers["Retry-After"]) > 0


def test_register_rate_limit_different_ips(client):
    """Các IP khác nhau thông qua X-Forwarded-For không bị chặn lẫn nhau."""
    for i in range(1, 4):
        res = client.post(
            "/auth/register",
            json={
                "email": f"ip_user_{i}@example.com",
                "full_name": f"IP User {i}",
                "password": "Password123",
            },
            headers={"X-Forwarded-For": f"192.168.1.{i}"},
        )
        assert res.status_code == 201

    # Request tiếp theo từ IP mới 192.168.1.99 vẫn đăng ký thành công
    res_new_ip = client.post(
        "/auth/register",
        json={
            "email": "ip_user_new@example.com",
            "full_name": "New IP User",
            "password": "Password123",
        },
        headers={"X-Forwarded-For": "192.168.1.99"},
    )
    assert res_new_ip.status_code == 201


# ==============================================================================
# 2. Rate Limit trên /auth/login-json (Tối đa 10 requests/phút từ 1 IP)
# ==============================================================================
def test_login_rate_limit_general_ip(client):
    """
    Gửi liên tiếp 10 request login từ 1 IP -> Được xử lý.
    Request thứ 11 -> Bị chặn với HTTP 429 Too Many Requests.
    """
    # Gửi 10 requests với các email khác nhau để kiểm tra rate limit theo IP
    for i in range(1, 11):
        res = client.post(
            "/auth/login-json",
            json={"email": f"diff_email_{i}@example.com", "password": "WrongPassword"},
        )
        # Các request này sai mật khẩu/email nhưng đều qua được lớp rate-limit -> 401
        assert res.status_code == 401

    # Request thứ 11 vượt quá rate limit IP -> 429
    res_rate_limited = client.post(
        "/auth/login-json",
        json={"email": "diff_email_11@example.com", "password": "WrongPassword"},
    )
    assert res_rate_limited.status_code == 429
    assert "quá nhiều yêu cầu đăng nhập" in res_rate_limited.json()["detail"].lower()
    assert "Retry-After" in res_rate_limited.headers


# ==============================================================================
# 3. Anti-Brute-Force: Khóa tài khoản sau 5 lần nhập sai mật khẩu liên tiếp
# ==============================================================================
def test_login_brute_force_lockout_json(client):
    """
    Đăng ký tài khoản hợp lệ.
    Thử đăng nhập sai mật khẩu 5 lần:
    - Lần 1 đến 4: Trả về HTTP 401 Unauthorized.
    - Lần 5: Kích hoạt khóa tài khoản tạm thời -> Trả về HTTP 429 với thông báo khóa.
    - Lần 6 trở đi: Bị chặn ngay từ vòng kiểm tra với HTTP 429 (không cần truy vấn DB).
    """
    target_email = "target_victim@example.com"
    correct_password = "CorrectPassword123"

    # Tạo user mẫu
    client.post(
        "/auth/register",
        json={
            "email": target_email,
            "full_name": "Target Victim",
            "password": correct_password,
        },
    )

    # 4 lần đầu nhập sai mật khẩu -> 401
    for attempt in range(1, 5):
        res = client.post(
            "/auth/login-json",
            json={"email": target_email, "password": f"WrongPass{attempt}"},
        )
        assert res.status_code == 401, f"Lần {attempt} phải là 401"

    # Lần thứ 5 nhập sai -> chạm ngưỡng max_failures (5) -> kích hoạt khóa -> 429
    res_5th = client.post(
        "/auth/login-json",
        json={"email": target_email, "password": "WrongPass5"},
    )
    assert res_5th.status_code == 429
    assert "tạm thời bị khóa" in res_5th.json()["detail"].lower()
    assert "Retry-After" in res_5th.headers

    # Lần thứ 6 (dù nhập đúng mật khẩu trong lúc đang bị khóa) -> vẫn bị chặn với 429
    res_6th = client.post(
        "/auth/login-json",
        json={"email": target_email, "password": correct_password},
    )
    assert res_6th.status_code == 429
    assert "tạm thời bị khóa" in res_6th.json()["detail"].lower()


def test_login_brute_force_lockout_form(client):
    """Kiểm tra cơ chế chống brute force trên endpoint form OAuth2 `/auth/login`."""
    target_email = "form_victim@example.com"
    correct_password = "CorrectPassword123"

    client.post(
        "/auth/register",
        json={
            "email": target_email,
            "full_name": "Form Victim",
            "password": correct_password,
        },
    )

    # 4 lần đầu nhập sai -> 401
    for attempt in range(1, 5):
        res = client.post(
            "/auth/login",
            data={"username": target_email, "password": f"WrongFormPass{attempt}"},
        )
        assert res.status_code == 401

    # Lần 5 -> 429
    res_5th = client.post(
        "/auth/login",
        data={"username": target_email, "password": "WrongFormPass5"},
    )
    assert res_5th.status_code == 429
    assert "tạm thời bị khóa" in res_5th.json()["detail"].lower()


# ==============================================================================
# 4. Đăng nhập thành công sẽ reset bộ đếm thất bại
# ==============================================================================
def test_login_success_resets_failure_counter(client):
    """
    Nhập sai mật khẩu 3 lần liên tiếp.
    Sau đó nhập đúng mật khẩu -> Đăng nhập thành công (200), bộ đếm thất bại được reset.
    Nhập sai tiếp 3 lần -> Vẫn chỉ là 401, không bị khóa (vì tổng liên tiếp mới là 3 < 5).
    """
    user_email = "counter_reset@example.com"
    password = "CorrectPassword123"

    client.post(
        "/auth/register",
        json={
            "email": user_email,
            "full_name": "Counter Reset Tester",
            "password": password,
        },
    )

    # Nhập sai 3 lần
    for _ in range(3):
        res = client.post(
            "/auth/login-json",
            json={"email": user_email, "password": "WrongPassword"},
        )
        assert res.status_code == 401

    # Nhập đúng mật khẩu -> 200 OK & reset counter
    res_success = client.post(
        "/auth/login-json",
        json={"email": user_email, "password": password},
    )
    assert res_success.status_code == 200
    assert "access_token" in res_success.json()

    # Nhập sai tiếp 3 lần nữa -> Vẫn là 401, không bị khóa vì đã reset
    for _ in range(3):
        res = client.post(
            "/auth/login-json",
            json={"email": user_email, "password": "WrongPassword"},
        )
        assert res.status_code == 401
