"""Router xử lý toàn bộ các tác vụ xác thực (Authentication & Authorization)."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.exceptions import AuthenticationError, DuplicateError, NotFoundError
from app.core.security import verify_password_reset_token
from app.dependencies.auth import get_current_user
from app.dependencies.get_db import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, RefreshTokenRequest, TokenResponse
from app.schemas.user import (
    ForgotPasswordRequest,
    PasswordChangeRequest,
    ResetPasswordRequest,
    UserCreate,
    UserRead,
)
from app.services import auth as auth_service
from app.services import user as user_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/health", summary="Kiểm tra trạng thái router auth")
def auth_health() -> dict[str, str]:
    return {"message": "Auth router is ready"}


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Đăng ký tài khoản người dùng mới (Task 9 - Chính)",
)
def register(
    user_in: UserCreate,
    db: Session = Depends(get_db),
) -> User:
    """
    Đăng ký tài khoản:
    - Kiểm tra email chưa tồn tại
    - Kiểm tra độ mạnh mật khẩu (ít nhất 6 ký tự)
    - Băm mật khẩu an toàn bằng bcrypt
    - Mặc định vai trò là 'user' nếu không chỉ định
    """
    try:
        new_user = user_service.create_user(db, user_in)
        return new_user
    except DuplicateError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Đăng nhập nhận Access Token + Refresh Token (Form data / Swagger UI) (Task 6 - Chính & Task 10 - Bonus)",
)
def login_form(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db),
) -> TokenResponse:
    """
    Đăng nhập tương thích chuẩn OAuth2 Password Request Form (tự động tích hợp nút Authorize trên Swagger UI):
    - username: truyền email của tài khoản
    - password: mật khẩu tài khoản
    """
    user = auth_service.authenticate_user(
        db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoặc mật khẩu không chính xác",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản người dùng đã bị vô hiệu hóa",
        )
    return auth_service.create_user_tokens(user)


@router.post(
    "/login-json",
    response_model=TokenResponse,
    summary="Đăng nhập nhận Access Token + Refresh Token bằng JSON body (Task 6 - Chính)",
)
def login_json(
    credentials: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Đăng nhập bằng JSON body `{'email': '...', 'password': '...'}`."""
    user = auth_service.authenticate_user(
        db, email=credentials.email, password=credentials.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoặc mật khẩu không chính xác",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản người dùng đã bị vô hiệu hóa",
        )
    return auth_service.create_user_tokens(user)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Lấy Access Token mới bằng Refresh Token (Task 10 - Bonus)",
)
def refresh_token(
    payload: RefreshTokenRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """
    Gia hạn phiên đăng nhập:
    Gửi refresh_token hợp lệ để nhận lại cặp access_token và refresh_token mới.
    """
    try:
        return auth_service.refresh_user_tokens(db, payload.refresh_token)
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get(
    "/me",
    response_model=UserRead,
    summary="Lấy thông tin người dùng hiện tại đang đăng nhập (Task 11 - Chính)",
)
def get_current_user_info(
    current_user: User = Depends(get_current_user),
) -> User:
    """Trả về thông tin chi tiết của người dùng sở hữu access token hiện tại."""
    return current_user


@router.post(
    "/forgot-password",
    summary="Yêu cầu đặt lại mật khẩu khi quên (Task 2 - Bonus)",
)
def forgot_password(
    req: ForgotPasswordRequest,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """
    Yêu cầu đặt lại mật khẩu:
    Tạo reset token có thời hạn ngắn (15 phút).
    Trả về thông báo và reset_token để phục vụ kiểm thử và mô phỏng gửi email.
    """
    try:
        reset_token = auth_service.request_password_reset(db, req.email)
        return {
            "message": "Đã tạo mã đặt lại mật khẩu thành công. Vui lòng kiểm tra email của bạn.",
            "reset_token": reset_token,
        }
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.post(
    "/reset-password",
    summary="Đặt lại mật khẩu mới bằng mã reset token (Task 2 - Bonus)",
)
def reset_password(
    req: ResetPasswordRequest,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """
    Xác thực reset token và cập nhật mật khẩu mới cho tài khoản.
    """
    email = verify_password_reset_token(req.token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mã đặt lại mật khẩu không hợp lệ hoặc đã hết hạn",
        )
    try:
        user_service.reset_user_password(db, email, req.new_password)
        return {"message": "Đặt lại mật khẩu thành công. Bạn có thể đăng nhập bằng mật khẩu mới."}
    except (NotFoundError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post(
    "/change-password",
    summary="Đổi mật khẩu người dùng (Task 3 - Bonus)",
)
def change_password(
    change_req: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """
    Đổi mật khẩu tài khoản đang đăng nhập:
    - Yêu cầu mật khẩu cũ chính xác
    - Mật khẩu mới tối thiểu 6 ký tự và không được trùng mật khẩu cũ
    """
    try:
        user_service.change_user_password(db, current_user, change_req)
        return {"message": "Đổi mật khẩu thành công."}
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
