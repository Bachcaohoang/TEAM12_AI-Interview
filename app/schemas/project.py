"""Schema dự án dành cho dữ liệu API."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


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