"""Model người dùng (User)."""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="USER")  # USER hoặc ADMIN
    is_active: Mapped[bool] = mapped_column(default=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # Quan hệ
    created_projects: Mapped[List["Project"]] = relationship("Project", back_populates="owner")
    memberships: Mapped[List["ProjectMember"]] = relationship("ProjectMember", back_populates="user")
    assigned_tasks: Mapped[List["Task"]] = relationship("Task", back_populates="assignee")