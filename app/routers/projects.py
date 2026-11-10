"""Endpoint mẫu cho nhóm dự án."""

from fastapi import APIRouter

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/sample")
def read_sample_project() -> dict[str, str]:
    return {"id": "sample-project", "name": "Dự án mẫu"}
