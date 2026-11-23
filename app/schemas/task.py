"""Schema Pydantic cho Entity Task."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.user import UserResponse


class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Tiêu đề công việc")
    description: Optional[str] = Field(None, description="Mô tả chi tiết công việc")
    due_date: Optional[datetime] = Field(None, description="Thời hạn hoàn thành (ISO 8601)")
    status: str = Field("TODO", description="Trạng thái: TODO, IN_PROGRESS, DONE")
    priority: str = Field("MEDIUM", description="Mức độ ưu tiên: LOW, MEDIUM, HIGH")


class ProjectTaskCreate(TaskBase):
    """Schema tạo Task qua endpoint POST /projects/{project_id}/tasks."""
    assignee_id: Optional[int] = Field(
        None,
        gt=0,
        examples=[None],
        description="ID người được giao việc (để trống hoặc null nếu chưa giao)",
    )


class TaskCreate(TaskBase):
    """Schema tạo Task đầy đủ project_id (giữ tương thích ngược)."""
    project_id: int = Field(..., gt=0)
    assignee_id: Optional[int] = Field(None, gt=0, examples=[None])


class TaskStatusUpdate(BaseModel):
    status: str = Field(..., description="Trạng thái mới: TODO, IN_PROGRESS, DONE")


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    assignee_id: Optional[int] = Field(None, gt=0, examples=[None])


class TaskResponse(TaskBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    assignee_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    assignee: Optional[UserResponse] = None


class PaginatedTaskResponse(BaseModel):
    """Schema phản hồi danh sách Task có phân trang và tổng số bản ghi."""
    page: int
    page_size: int
    total: int
    total_pages: int
    has_next: bool
    has_previous: bool
    items: list[TaskResponse]


# Alias tương thích
TaskRead = TaskResponse