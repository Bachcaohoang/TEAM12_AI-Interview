"""Schema dự án dành cho dữ liệu API."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    status: Optional[str] = Field("in_progress", description="pending, in_progress, completed, cancelled")


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    status: Optional[str] = Field(None, description="pending, in_progress, completed, cancelled")


class ProjectRead(ProjectBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ProjectMemberAdd(BaseModel):
    user_id: int = Field(..., gt=0)
    role: str = Field("MEMBER", description="OWNER, MANAGER, MEMBER")


class ProjectMemberResponse(BaseModel):
    project_id: int
    user_id: int
    role: str

    model_config = ConfigDict(from_attributes=True)


class ProjectMemberItemResponse(BaseModel):
    user_id: int
    role: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    joined_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

ProjectResponse = ProjectRead

class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    status: Optional[str] = Field("in_progress", description="pending, in_progress, completed, cancelled")

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Tên dự án không được để trống hoặc chỉ chứa khoảng trắng.")
        return stripped


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    status: Optional[str] = Field(None, description="pending, in_progress, completed, cancelled")

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            stripped = v.strip()
            if not stripped:
                raise ValueError("Tên dự án không được để trống hoặc chỉ chứa khoảng trắng.")
            return stripped
        return v

class TaskStatusBreakdown(BaseModel):
    TODO: int = 0
    IN_PROGRESS: int = 0
    DONE: int = 0


class AssigneeTaskSummary(BaseModel):
    assignee_id: Optional[int] = None
    full_name: str
    email: Optional[str] = None
    total_tasks: int = 0
    todo: int = 0
    in_progress: int = 0
    done: int = 0
    completion_rate: float = 0.0


class ProjectDashboardResponse(BaseModel):
    project_id: int
    project_name: str
    total_tasks: int
    completed_tasks: int
    completion_rate: float
    tasks_by_status: TaskStatusBreakdown
    tasks_by_assignee: list[AssigneeTaskSummary]