"""Pydantic schemas cho Thông báo hệ thống (Notification)."""

from datetime import datetime
from pydantic import BaseModel, ConfigDict


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    type: str
    title: str
    message: str
    is_read: bool
    project_id: int | None = None
    task_id: int | None = None
    created_at: datetime


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    total: int
    unread_count: int


class NotificationReadAllResponse(BaseModel):
    updated_count: int
