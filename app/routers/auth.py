"""Endpoint xử lý xác thực (Auth): Đăng ký, Đăng nhập và kiểm tra Lỗi nghiệp vụ."""

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import (
    EmailAlreadyExistsException,
    InvalidCredentialsException,
)
from app.core.security import hash_password, verify_password
from app.dependencies.get_db import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Hàm tạo JWT Token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)) -> Any:
    """POST /auth/register: Đăng ký tài khoản, xử lý lỗi trùng Email (HTTP 400)."""
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise EmailAlreadyExistsException()

    user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=hash_password(user_in.password),
        role="USER",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> dict[str, str]:
    """POST /auth/login: Đăng nhập, xử lý sai Credentials (HTTP 401)."""
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise InvalidCredentialsException()

    access_token = create_access_token(data={"sub": user.email, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}