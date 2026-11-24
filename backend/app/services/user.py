"""Nghiệp vụ quản lý người dùng."""

from typing import Optional
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.exceptions import DuplicateError, NotFoundError
from app.core.security import hash_password, validate_password_strength, verify_password
from app.models.user import User
from app.schemas.user import PasswordChangeRequest, UserCreate, UserProfileUpdate


def normalize_full_name(full_name: str) -> str:
    """Chuẩn hóa họ tên: loại bỏ khoảng trắng thừa."""
    return " ".join(full_name.strip().split())


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Tìm user theo ID."""
    return db.scalar(select(User).where(User.id == user_id))


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Tìm user theo Email."""
    return db.scalar(select(User).where(User.email == email.strip().lower()))


def get_users(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None,
    role: Optional[str] = None,
) -> list[User]:
    """Lấy danh sách người dùng có hỗ trợ phân trang và tìm kiếm."""
    query = select(User)
    if search:
        pattern = f"%{search.strip()}%"
        query = query.where(
            or_(User.email.ilike(pattern), User.full_name.ilike(pattern))
        )
    if role:
        query = query.where(User.role == role.strip())

    query = query.offset(skip).limit(limit).order_by(User.id.desc())
    return list(db.scalars(query).all())


def create_user(db: Session, user_in: UserCreate) -> User:
    """Đăng ký người dùng mới vào hệ thống."""
    email_clean = user_in.email.strip().lower()
    if get_user_by_email(db, email_clean):
        raise DuplicateError(f"Email '{email_clean}' đã được đăng ký.")

    is_valid, msg = validate_password_strength(user_in.password)
    if not is_valid:
        raise ValueError(msg)

    user = User(
        email=email_clean,
        full_name=normalize_full_name(user_in.full_name),
        hashed_password=hash_password(user_in.password),
        role=user_in.role or "user",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user_profile(
    db: Session, user: User, profile_in: UserProfileUpdate
) -> User:
    """Cập nhật thông tin hồ sơ của người dùng."""
    user.full_name = normalize_full_name(profile_in.full_name)
    db.commit()
    db.refresh(user)
    return user


def change_user_password(
    db: Session, user: User, change_req: PasswordChangeRequest
) -> User:
    """Đổi mật khẩu người dùng."""
    if not verify_password(change_req.old_password, user.hashed_password):
        raise ValueError("Mật khẩu hiện tại không chính xác.")

    if change_req.old_password == change_req.new_password:
        raise ValueError("Mật khẩu mới không được trùng với mật khẩu cũ.")

    is_valid, msg = validate_password_strength(change_req.new_password)
    if not is_valid:
        raise ValueError(msg)

    user.hashed_password = hash_password(change_req.new_password)
    db.commit()
    db.refresh(user)
    return user


def reset_user_password(db: Session, email: str, new_password: str) -> User:
    """Đặt lại mật khẩu cho người dùng thông qua quy trình quên mật khẩu."""
    user = get_user_by_email(db, email)
    if not user:
        raise NotFoundError(f"Không tìm thấy người dùng với email {email}.")

    is_valid, msg = validate_password_strength(new_password)
    if not is_valid:
        raise ValueError(msg)

    user.hashed_password = hash_password(new_password)
    db.commit()
    db.refresh(user)
    return user
