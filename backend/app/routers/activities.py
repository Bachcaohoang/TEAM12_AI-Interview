"""Router nhật ký hoạt động dự án (Audit Trail)."""

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.dependencies.auth import get_current_user
from app.dependencies.get_db import get_db
from app.models.user import User
from app.schemas.activity import PaginatedActivityResponse
from app.services import activity as activity_service

router = APIRouter(tags=["Activities"])


@router.get(
    "/projects/{project_id}/activities",
    response_model=PaginatedActivityResponse,
    status_code=status.HTTP_200_OK,
    summary="Lấy lịch sử hoạt động của dự án",
    description="Truy xuất dòng thời gian các hoạt động (tạo dự án, cập nhật thông tin, tạo/sửa/đổi trạng thái/xóa task). Yêu cầu người dùng là thành viên dự án.",
    responses={
        200: {"description": "Lấy danh sách nhật ký hoạt động thành công kèm metadata phân trang."},
        400: {"description": "Tham số phân trang không hợp lệ (page < 1 hoặc page_size vượt quá 100)."},
        403: {"description": "Người dùng không thuộc dự án này."},
        404: {"description": "Dự án không tồn tại hoặc đã bị xóa mềm."},
    },
)
def list_project_activities(
    project_id: int = Path(..., gt=0, description="ID của dự án cần lấy lịch sử hoạt động"),
    page: int = Query(1, description="Trang hiện tại (>= 1)"),
    page_size: int = Query(10, description="Số bản ghi mỗi trang (1-100)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    try:
        return activity_service.get_project_activities(
            db,
            project_id=project_id,
            current_user=current_user,
            page=page,
            page_size=page_size,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
