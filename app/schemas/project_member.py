"""Schema Pydantic cho Entity ProjectMember."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.user import UserResponse



class ProjectMemberBase(BaseModel):
    role: str = "MEMBER"


class ProjectMemberAdd(ProjectMemberBase):
    user_id: int = Field(..., gt=0, examples=[1])


class ProjectMemberUpdate(BaseModel):
    role: str


class ProjectMemberResponse(ProjectMemberBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    user_id: int
    joined_at: datetime
    user: Optional[UserResponse] = None