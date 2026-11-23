"""Model Thành viên Dự án (ProjectMember - Bảng trung gian)."""

from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ProjectMember(Base):
    __tablename__ = "project_members"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="MEMBER")  # OWNER, MANAGER, MEMBER
    
    joined_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Quan hệ
    project: Mapped["Project"] = relationship("Project", back_populates="members")
    user: Mapped["User"] = relationship("User", back_populates="memberships")

    # Đảm bảo 1 user không bị trùng lặp trong 1 dự án
    __table_args__ = (
        UniqueConstraint("project_id", "user_id", name="uq_project_user"),
    )