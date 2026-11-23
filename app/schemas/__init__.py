from app.schemas.auth import LoginRequest, RefreshTokenRequest, TokenResponse
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate
from app.schemas.project_member import (
    ProjectMemberAdd,
    ProjectMemberBase,
    ProjectMemberResponse,
    ProjectMemberUpdate,
)
from app.schemas.activity import ActivityLogResponse, PaginatedActivityResponse
from app.schemas.attachment import AttachmentResponse, PaginatedAttachmentResponse
from app.schemas.comment import (
    CommentCreate,
    CommentResponse,
    CommentUpdate,
    PaginatedCommentResponse,
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

# Alias tương thích
ProjectMemberCreate = ProjectMemberAdd

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
    "ProjectCreate",
    "ProjectRead",
    "ProjectUpdate",
    "ProjectMemberBase",
    "ProjectMemberAdd",
    "ProjectMemberCreate",
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
