import os
import sys

# Thêm thư mục gốc vào sys.path để import được app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings

from app.db.base import Base
from app.dependencies.get_db import get_db
from app.main import app
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.user import User


# Thiết lập SQLite in-memory cho test
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


def create_test_token(email: str, role: str = "USER") -> str:
    """Tạo JWT token giả lập cho test."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=30)
    to_encode = {"sub": email, "role": role, "exp": expire}
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


@pytest.fixture(autouse=True)
def setup_database():
    """Tạo mới cấu trúc bảng trước mỗi test và chèn dữ liệu mẫu."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    # Tạo 3 users:
    # 1. user1 (Owner của Project 1, Member của Project 2)
    # 2. user2 (Member của Project 1)
    # 3. outsider (Không thuộc Project 1)
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

    # Tạo Project 1: owner là user1
    proj1 = Project(
        name="AI Interview System",
        description="Core backend for AI Interview",
        owner_id=user1.id,
    )
    db.add(proj1)
    db.commit()

    # Thêm user2 làm member của Project 1
    pm = ProjectMember(
        project_id=proj1.id,
        user_id=user2.id,
        role="MEMBER",
    )
    db.add(pm)
    db.commit()

    db.close()
    yield
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


def test_get_project_detail_unauthenticated():
    """1. Gọi endpoint khi chưa đăng nhập (không có token) -> Phải trả về 401 Unauthorized."""
    response = client.get("/projects/1")
    assert response.status_code == 401


def test_get_project_detail_by_owner():
    """2. Chủ sở hữu dự án (Owner) xem chi tiết -> Phải trả về 200 OK với đầy đủ thông tin."""
    token = create_test_token("owner@test.com")
    response = client.get(
        "/projects/1",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "AI Interview System"
    assert data["owner_id"] is not None
    assert "members" in data
    assert len(data["members"]) == 1
    assert data["members"][0]["user"]["email"] == "member@test.com"


def test_get_project_detail_by_member():
    """3. Thành viên dự án (Member) xem chi tiết -> Phải trả về 200 OK."""
    token = create_test_token("member@test.com")
    response = client.get(
        "/projects/1",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["name"] == "AI Interview System"


def test_get_project_detail_by_non_member():
    """4. Người dùng không thuộc dự án truy cập -> Phải trả về 403 Forbidden."""
    token = create_test_token("outsider@test.com")
    response = client.get(
        "/projects/1",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == 403
    assert "thành viên" in data["error"]["message"].lower()


def test_get_project_detail_not_found():
    """5. Dự án không tồn tại -> Phải trả về 404 Not Found."""
    token = create_test_token("owner@test.com")
    response = client.get(
        "/projects/9999",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == 404
    assert "dự án không tồn tại" in data["error"]["message"].lower()


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
    """7. Người dùng đăng nhập tạo dự án thành công -> Trả về 201 và tự động trở thành OWNER trong DB."""
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

    # Kiểm tra trực tiếp trong Database
    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.email == "outsider@test.com").first()
        assert user is not None
        assert data["owner_id"] == user.id

        # Kiểm tra bản ghi Project
        project = db.query(Project).filter(Project.id == new_project_id).first()
        assert project is not None
        assert project.owner_id == user.id

        # Kiểm tra tự động trở thành OWNER trong ProjectMember
        member = (
            db.query(ProjectMember)
            .filter(
                ProjectMember.project_id == new_project_id,
                ProjectMember.user_id == user.id,
            )
            .first()
        )
        assert member is not None
        assert member.role == "OWNER"
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
    """10. Gửi thiếu trường bắt buộc 'name' -> Phải trả về 400 Bad Request."""
    token = create_test_token("owner@test.com")
    response = client.post(
        "/projects",
        json={"description": "Thiếu tên dự án"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == 400
    assert "dữ liệu đầu vào không hợp lệ" in data["error"]["message"].lower()


def test_created_project_owner_can_read_detail():
    """11. Người tạo dự án tự động xem được chi tiết dự án vừa tạo với quyền OWNER."""
    token = create_test_token("outsider@test.com")
    create_res = client.post(
        "/projects",
        json={"name": "Dự án xem chi tiết", "description": "Test read detail"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create_res.status_code == 201
    proj_id = create_res.json()["id"]

    # Xem chi tiết dự án vừa tạo
    detail_res = client.get(
        f"/projects/{proj_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    assert detail_data["name"] == "Dự án xem chi tiết"
    assert len(detail_data["members"]) == 1
    assert detail_data["members"][0]["role"] == "OWNER"
    assert detail_data["members"][0]["user"]["email"] == "outsider@test.com"

