"""Các schema Pydantic dùng kiểm tra dữ liệu vào và ra API."""

from app.schemas.activity import ActivityLogResponse, PaginatedActivityResponse
from app.schemas.attachment import AttachmentResponse, PaginatedAttachmentResponse
from app.schemas.auth import LoginRequest, RefreshTokenRequest, TokenResponse
from app.schemas.comment import (
    CommentCreate,
    CommentResponse,
    CommentUpdate,
    PaginatedCommentResponse,
)
from app.schemas.project import (
    ProjectBase,
    ProjectCreate,
    ProjectRead,
    ProjectResponse,
    ProjectUpdate,
)
from app.schemas.project_member import (
    ProjectMemberAdd,
    ProjectMemberBase,
    ProjectMemberResponse,
    ProjectMemberUpdate,
)
from app.schemas.task import (
    PaginatedTaskResponse,
    ProjectTaskCreate,
    TaskBase,
    TaskCreate,
    TaskRead,
    TaskResponse,
    TaskStatusUpdate,
    TaskUpdate,
)
from app.schemas.user import (
    ForgotPasswordRequest,
    PasswordChangeRequest,
    ResetPasswordRequest,
    UserBase,
    UserCreate,
    UserProfileUpdate,
    UserRead,
    UserResponse,
    UserUpdate,
)

__all__ = [
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserRead",
    "UserProfileUpdate",
    "PasswordChangeRequest",
    "ForgotPasswordRequest",
    "ResetPasswordRequest",
    "LoginRequest",
    "TokenResponse",
    "RefreshTokenRequest",
    "ProjectBase",
    "ProjectCreate",
    "ProjectRead",
    "ProjectResponse",
    "ProjectUpdate",
    "ProjectMemberBase",
    "ProjectMemberAdd",
    "ProjectMemberUpdate",
    "ProjectMemberResponse",
    "TaskBase",
    "TaskCreate",
    "ProjectTaskCreate",
    "TaskUpdate",
    "TaskStatusUpdate",
    "TaskResponse",
    "TaskRead",
    "PaginatedTaskResponse",
    "ActivityLogResponse",
    "PaginatedActivityResponse",
    "CommentCreate",
    "CommentUpdate",
    "CommentResponse",
    "PaginatedCommentResponse",
    "AttachmentResponse",
    "PaginatedAttachmentResponse",
]
