"""Endpoint quản lý nhóm công việc (Task)."""

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.dependencies.auth import get_current_user
from app.dependencies.get_db import get_db
from app.models.user import User
from app.schemas.task import TaskResponse, TaskStatusUpdate, TaskUpdate
from app.services import task as task_service

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get(
    "/sample",
    summary="Lấy công việc mẫu",
    description="Endpoint mẫu trả về thông tin công việc kiểm tra kết nối định tuyến.",
    status_code=status.HTTP_200_OK,
)
def read_sample_task() -> dict[str, str]:
    return {"id": "sample-task", "title": "Công việc mẫu"}


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Lấy chi tiết công việc theo ID",
    description="Truy xuất thông tin chi tiết một công việc. Bắt buộc kiểm tra quyền người dùng phải thuộc dự án chứa công việc.",
    responses={
        200: {"description": "Lấy chi tiết công việc thành công."},
        401: {"description": "Chưa đăng nhập / Token không hợp lệ."},
        403: {"description": "Không có quyền xem công việc này (không thuộc dự án)."},
        404: {"description": "Không tìm thấy công việc với ID chỉ định."},
    },
)
def get_task_detail(
    task_id: int = Path(..., gt=0, description="ID của công việc cần xem chi tiết"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskResponse:
    try:
        return task_service.get_task_by_id(
            db=db,
            task_id=task_id,
            current_user=current_user,
        )
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except PermissionDeniedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc


@router.put(
    "/{task_id}",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Cập nhật toàn bộ thông tin công việc (PUT)",
    description="Cập nhật thông tin công việc với kiểm tra phân quyền chặt chẽ chống IDOR. Chỉ Owner/Manager dự án hoặc người được giao việc (Assignee) mới có quyền.",
    responses={
        200: {"description": "Cập nhật công việc thành công."},
        400: {"description": "Dữ liệu cập nhật hoặc chuyển trạng thái không hợp lệ."},
        401: {"description": "Chưa đăng nhập / Token không hợp lệ."},
        403: {"description": "Không có quyền sửa công việc này."},
        404: {"description": "Không tìm thấy công việc hoặc dự án."},
    },
)
def update_task_put(
    task_id: int = Path(..., gt=0, description="ID của công việc cần cập nhật"),
    task_in: TaskUpdate = ...,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskResponse:
    try:
        return task_service.update_task(
            db=db,
            task_id=task_id,
            task_in=task_in,
            current_user=current_user,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.patch(
    "/{task_id}",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Cập nhật một phần công việc theo ID (PATCH)",
    description="Cập nhật các trường được truyền lên (title, description, due_date, status, priority, assignee_id), bảo toàn các trường không gửi lên. Áp dụng quy tắc phân quyền RBAC và kiểm tra quy trình chuyển trạng thái.",
    responses={
        200: {"description": "Cập nhật một phần công việc thành công."},
        400: {"description": "Giá trị cập nhật không hợp lệ (hạn chót quá khứ, sai workflow trạng thái...)."},
        401: {"description": "Chưa đăng nhập / Token không hợp lệ."},
        403: {"description": "Không có quyền sửa công việc này."},
        404: {"description": "Không tìm thấy công việc hoặc dự án."},
    },
)
def update_task_endpoint(
    task_in: TaskUpdate,
    task_id: int = Path(..., gt=0, description="ID của công việc"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskResponse:
    try:
        return task_service.update_task(
            db=db,
            task_id=task_id,
            task_in=task_in,
            current_user=current_user,
        )
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except PermissionDeniedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.patch(
    "/{task_id}/status",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Đổi trạng thái công việc",
    description="Chuyển trạng thái công việc (TODO -> IN_PROGRESS -> DONE). Tự động ghi lại lịch sử hoạt động và gửi thông báo đến các bên liên quan.",
    responses={
        200: {"description": "Đổi trạng thái công việc thành công."},
        400: {"description": "Trạng thái không hợp lệ hoặc sai quy trình chuyển đổi."},
        401: {"description": "Chưa đăng nhập / Token không hợp lệ."},
        403: {"description": "Không có quyền thay đổi trạng thái công việc này."},
        404: {"description": "Không tìm thấy công việc."},
    },
)
def change_task_status(
    task_id: int = Path(..., gt=0, description="ID của công việc"),
    status_in: TaskStatusUpdate = ...,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskResponse:
    try:
        return task_service.change_task_status(
            db=db,
            task_id=task_id,
            status=status_in.status,
            current_user=current_user,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Xóa công việc theo ID",
    description="Xóa công việc và toàn bộ tệp đính kèm vật lý liên quan (chỉ chủ dự án OWNER, quản lý dự án MANAGER hoặc Admin hệ thống).",
    responses={
        204: {"description": "Xóa công việc thành công."},
        401: {"description": "Chưa đăng nhập / Token không hợp lệ."},
        403: {"description": "Không có quyền xóa công việc này."},
        404: {"description": "Không tìm thấy công việc hoặc dự án."},
    },
)
def delete_task(
    task_id: int = Path(..., gt=0, description="ID của công việc cần xóa"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    try:
        task_service.delete_task(db=db, task_id=task_id, current_user=current_user)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
