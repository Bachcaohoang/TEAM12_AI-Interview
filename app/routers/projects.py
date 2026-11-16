"""Endpoint xử lý các nghiệp vụ liên quan đến dự án (Projects)."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.dependencies.get_db import get_db
from app.models.user import User
from app.schemas.project import ProjectDetailResponse
from app.services.project import get_project_detail

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/sample")
def read_sample_project() -> dict[str, str]:
    return {"id": "sample-project", "name": "Dự án mẫu"}


@router.get(
    "/{project_id}",
    response_model=ProjectDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Xem thông tin chi tiết dự án",
    description="Chỉ thành viên của dự án (hoặc chủ sở hữu) mới có quyền xem thông tin chi tiết.",
)
def read_project_detail(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_project_detail(db=db, project_id=project_id, current_user=current_user)

