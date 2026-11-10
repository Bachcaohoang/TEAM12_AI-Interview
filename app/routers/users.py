"""Endpoint mẫu cho nhóm người dùng."""

from fastapi import APIRouter

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/sample")
def read_sample_user() -> dict[str, str]:
    return {"id": "sample-user", "name": "Người dùng mẫu"}
