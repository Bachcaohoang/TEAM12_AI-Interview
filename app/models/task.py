"""Model Công việc (Task)."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.user import User


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="TODO")  # TODO, IN_PROGRESS, DONE
    priority: Mapped[str] = mapped_column(String(50), default="MEDIUM")  # LOW, MEDIUM, HIGH
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    assignee_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # Quan hệ
    project: Mapped["Project"] = relationship("Project", back_populates="tasks")
    assignee: Mapped[Optional["User"]] = relationship("User", back_populates="assigned_tasks")