"""Schema nhật ký hoạt động."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.schemas.user import UserResponse


class ActivityLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: Optional[int] = None
    project_id: int
    action: str
    entity_type: str
    entity_id: Optional[int] = None
    description: str
    created_at: Optional[datetime] = None
    user: Optional[UserResponse] = None


class PaginatedActivityResponse(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int
    has_next: bool
    has_previous: bool
    items: list[ActivityLogResponse]
