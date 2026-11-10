"""Endpoint mẫu cho nhóm xác thực."""

from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/health")
def auth_health() -> dict[str, str]:
    return {"message": "Auth router is ready"}
