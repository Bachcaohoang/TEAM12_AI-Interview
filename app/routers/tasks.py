"""Endpoint mẫu cho nhóm công việc."""

from fastapi import APIRouter

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/sample")
def read_sample_task() -> dict[str, str]:
    return {"id": "sample-task", "title": "Công việc mẫu"}
