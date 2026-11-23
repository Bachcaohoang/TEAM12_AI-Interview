"""Router tệp đính kèm công việc (Task Attachments)."""

from fastapi import APIRouter, Depends, File, HTTPException, Path, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.dependencies.auth import get_current_user
from app.dependencies.get_db import get_db
from app.models.user import User
from app.schemas.attachment import AttachmentResponse, PaginatedAttachmentResponse
from app.services import attachment as attachment_service

router = APIRouter(tags=["Attachments"])


@router.post(
    "/tasks/{task_id}/attachments",
    response_model=AttachmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tải lên tệp đính kèm cho công việc",
    description="Tải lên file đính kèm (tối đa 10MB) cho công việc. Người dùng phải là thành viên dự án chứa công việc.",
    responses={
        201: {"description": "Tải lên tệp đính kèm thành công."},
        400: {"description": "Kích thước tệp vượt quá giới hạn cho phép hoặc file không hợp lệ."},
        403: {"description": "Người dùng không thuộc dự án chứa công việc."},
        404: {"description": "Không tìm thấy công việc."},
    },
)
async def upload_task_attachment(
    task_id: int = Path(..., gt=0, description="ID của công việc cần đính kèm tệp"),
    file: UploadFile = File(..., description="Tệp tin cần tải lên"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return await attachment_service.upload_attachment(
            db, task_id=task_id, file=file, current_user=current_user
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get(
    "/tasks/{task_id}/attachments",
    response_model=PaginatedAttachmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Danh sách tệp đính kèm của công việc",
    description="Lấy danh sách các tệp đính kèm của công việc kèm phân trang (page, page_size).",
    responses={
        200: {"description": "Lấy danh sách tệp đính kèm thành công."},
        400: {"description": "Tham số phân trang không hợp lệ."},
        403: {"description": "Người dùng không thuộc dự án chứa công việc."},
        404: {"description": "Không tìm thấy công việc."},
    },
)
def list_task_attachments(
    task_id: int = Path(..., gt=0, description="ID của công việc"),
    page: int = Query(1, ge=1, description="Trang hiện tại (>= 1)"),
    page_size: int = Query(10, ge=1, le=100, description="Số bản ghi mỗi trang (1-100)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    try:
        return attachment_service.list_task_attachments(
            db,
            task_id=task_id,
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


@router.get(
    "/attachments/{attachment_id}/download",
    status_code=status.HTTP_200_OK,
    summary="Tải xuống tệp đính kèm",
    description="Tải về file đính kèm vật lý dựa trên ID. Yêu cầu người dùng thuộc dự án chứa tệp.",
    responses={
        200: {
            "description": "Tải về tệp tin thành công.",
            "content": {"application/octet-stream": {}},
        },
        403: {"description": "Không có quyền truy cập tệp đính kèm này."},
        404: {"description": "Tệp đính kèm không tồn tại trên hệ thống hoặc ổ đĩa."},
    },
)
def download_attachment(
    attachment_id: int = Path(..., gt=0, description="ID của tệp đính kèm cần tải về"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        attachment, path = attachment_service.get_attachment_for_download(
            db, attachment_id=attachment_id, current_user=current_user
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return FileResponse(
        path=str(path),
        filename=attachment.filename,
        media_type=attachment.content_type,
    )


@router.delete(
    "/attachments/{attachment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Xóa tệp đính kèm",
    description="Xóa bản ghi và xóa file vật lý an toàn khỏi hệ thống (chỉ người tải lên, chủ dự án hoặc Admin).",
    responses={
        204: {"description": "Xóa tệp đính kèm thành công."},
        403: {"description": "Không có quyền xóa tệp đính kèm này."},
        404: {"description": "Tệp đính kèm không tồn tại."},
    },
)
def delete_attachment(
    attachment_id: int = Path(..., gt=0, description="ID của tệp đính kèm cần xóa"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    try:
        attachment_service.delete_attachment(
            db, attachment_id=attachment_id, current_user=current_user
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
