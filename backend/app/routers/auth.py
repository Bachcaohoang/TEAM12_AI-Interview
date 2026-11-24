"""Router xử lý toàn bộ các tác vụ xác thực (Authentication & Authorization)."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.exceptions import AuthenticationError, DuplicateError, NotFoundError
from app.core.rate_limiter import (
    check_login_security,
    check_rate_limit,
    handle_login_failure,
    handle_login_success,
)
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

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.get(
    "/health",
    summary="Kiểm tra trạng thái router Auth",
    description="Kiểm tra router xác thực sẵn sàng nhận yêu cầu.",
    status_code=status.HTTP_200_OK,
)
def auth_health() -> dict[str, str]:
    return {"message": "Auth router is ready"}


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Đăng ký tài khoản người dùng mới",
    description="""
Đăng ký tài khoản người dùng mới:
* Giới hạn tần suất: tối đa 3 requests/phút từ 1 địa chỉ IP (chống spam).
* Kiểm tra tính duy nhất của email.
* Kiểm tra độ mạnh mật khẩu (tối thiểu 6 ký tự).
* Băm mật khẩu an toàn bằng bcrypt.
    """,
    responses={
        201: {"description": "Đăng ký tài khoản thành công."},
        400: {"description": "Email đã được sử dụng."},
        422: {"description": "Dữ liệu hoặc mật khẩu không hợp lệ."},
        429: {"description": "Gửi yêu cầu quá nhanh, vượt giới hạn rate limit."},
    },
)
def register(
    user_in: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    check_rate_limit(request, prefix="register", max_requests=3, window_seconds=60)

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
    status_code=status.HTTP_200_OK,
    summary="Đăng nhập nhận JWT Token (Form Data / Swagger UI)",
    description="Đăng nhập OAuth2 Password Flow chuẩn Form Data để tích hợp trực tiếp với nút Authorize trên Swagger UI. Kèm cơ chế khóa tạm thời nếu nhập sai liên tiếp 5 lần.",
    responses={
        200: {"description": "Đăng nhập thành công, trả về Access Token & Refresh Token."},
        401: {"description": "Email hoặc mật khẩu không chính xác."},
        403: {"description": "Tài khoản người dùng đã bị vô hiệu hóa."},
        429: {"description": "Vượt quá giới hạn thử đăng nhập hoặc tài khoản đang bị khóa tạm thời."},
    },
)
def login_form(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    request: Request,
    db: Session = Depends(get_db),
) -> TokenResponse:
    check_login_security(request, email=form_data.username, max_requests=10, window_seconds=60)

    user = auth_service.authenticate_user(
        db, email=form_data.username, password=form_data.password
    )
    if not user:
        handle_login_failure(request, email=form_data.username, max_failures=5, lockout_seconds=60)
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

    handle_login_success(request, email=form_data.username)
    return auth_service.create_user_tokens(user)


@router.post(
    "/login-json",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Đăng nhập nhận JWT Token bằng JSON Body",
    description="Đăng nhập nhận cặp Access Token và Refresh Token bằng payload JSON. Tích hợp chống brute-force và rate limiting.",
    responses={
        200: {"description": "Đăng nhập thành công, trả về Access Token & Refresh Token."},
        401: {"description": "Email hoặc mật khẩu không chính xác."},
        403: {"description": "Tài khoản người dùng đã bị vô hiệu hóa."},
        429: {"description": "Vượt quá giới hạn thử đăng nhập hoặc tài khoản đang bị khóa tạm thời."},
    },
)
def login_json(
    credentials: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> TokenResponse:
    check_login_security(request, email=credentials.email, max_requests=10, window_seconds=60)

    user = auth_service.authenticate_user(
        db, email=credentials.email, password=credentials.password
    )
    if not user:
        handle_login_failure(request, email=credentials.email, max_failures=5, lockout_seconds=60)
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

    handle_login_success(request, email=credentials.email)
    return auth_service.create_user_tokens(user)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Lấy cặp Token mới bằng Refresh Token",
    description="Gia hạn phiên đăng nhập khi Access Token hết hạn bằng cách cung cấp Refresh Token hợp lệ.",
    responses={
        200: {"description": "Cấp mới token thành công."},
        401: {"description": "Refresh token không hợp lệ hoặc đã hết hạn."},
        404: {"description": "Người dùng không còn tồn tại."},
    },
)
def refresh_token(
    payload: RefreshTokenRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
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
    status_code=status.HTTP_200_OK,
    summary="Lấy thông tin người dùng hiện tại đang đăng nhập",
    description="Truy xuất thông tin hồ sơ của người dùng sở hữu Access Token đang gửi trong header Authorization.",
    responses={
        200: {"description": "Lấy thông tin người dùng thành công."},
        401: {"description": "Chưa đăng nhập / Token không hợp lệ."},
    },
)
def get_current_user_info(
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user


@router.post(
    "/forgot-password",
    status_code=status.HTTP_200_OK,
    summary="Yêu cầu đặt lại mật khẩu khi quên",
    description="Tạo mã Token đặt lại mật khẩu có thời hạn ngắn (15 phút) gửi tới email của tài khoản.",
    responses={
        200: {"description": "Tạo mã reset mật khẩu thành công."},
        404: {"description": "Không tìm thấy tài khoản với email yêu cầu."},
    },
)
def forgot_password(
    req: ForgotPasswordRequest,
    db: Session = Depends(get_db),
) -> dict[str, str]:
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
    status_code=status.HTTP_200_OK,
    summary="Đặt lại mật khẩu mới bằng mã Reset Token",
    description="Xác thực reset token và cập nhật mật khẩu mới cho tài khoản người dùng.",
    responses={
        200: {"description": "Đặt lại mật khẩu thành công."},
        400: {"description": "Token không hợp lệ, hết hạn hoặc mật khẩu không đạt yêu cầu."},
    },
)
def reset_password(
    req: ResetPasswordRequest,
    db: Session = Depends(get_db),
) -> dict[str, str]:
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
    status_code=status.HTTP_200_OK,
    summary="Đổi mật khẩu người dùng đang đăng nhập",
    description="Đổi mật khẩu tài khoản hiện tại: yêu cầu mật khẩu cũ chính xác và mật khẩu mới tối thiểu 6 ký tự.",
    responses={
        200: {"description": "Đổi mật khẩu thành công."},
        400: {"description": "Mật khẩu cũ không đúng, hoặc mật khẩu mới trùng mật khẩu cũ / không đạt yêu cầu."},
        401: {"description": "Chưa đăng nhập / Token không hợp lệ."},
    },
)
def change_password(
    change_req: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    try:
        user_service.change_user_password(db, current_user, change_req)
        return {"message": "Đổi mật khẩu thành công."}
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
