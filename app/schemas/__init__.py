from app.schemas.auth import LoginRequest, RefreshTokenRequest, TokenResponse
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate
from app.schemas.project_member import (
    ProjectMemberAdd,
    ProjectMemberBase,
    ProjectMemberResponse,
    ProjectMemberUpdate,
)
from app.schemas.task import TaskBase, TaskCreate, TaskResponse, TaskUpdate
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
from app.schemas.task import (
    ProjectTaskCreate,
    TaskBase,
    TaskCreate,
    TaskRead,
    TaskResponse,
    TaskUpdate,
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
    "TaskUpdate",
    "TaskResponse",
    "TaskBase",
    "TaskCreate",
    "ProjectTaskCreate",
    "TaskUpdate",
    "TaskResponse",
    "TaskRead",
]
