"""Schema tệp đính kèm."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.schemas.user import UserResponse


class AttachmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    content_type: str
    file_size: int
    task_id: int
    user_id: int
    created_at: Optional[datetime] = None
    uploader: Optional[UserResponse] = None


class PaginatedAttachmentResponse(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int
    has_next: bool
    has_previous: bool
    items: list[AttachmentResponse]
