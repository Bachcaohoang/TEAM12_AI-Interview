"""Router tệp đính kèm công việc."""

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.dependencies.auth import get_current_user
from app.dependencies.get_db import get_db
from app.models.user import User
from app.schemas.attachment import AttachmentResponse, PaginatedAttachmentResponse
from app.services import attachment as attachment_service

router = APIRouter(tags=["attachments"])


@router.post(
    "/tasks/{task_id}/attachments",
    response_model=AttachmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tải lên tệp đính kèm cho công việc",
)
async def upload_task_attachment(
    task_id: int,
    file: UploadFile = File(...),
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
    summary="Danh sách tệp đính kèm của công việc",
)
def list_task_attachments(
    task_id: int,
    page: int = Query(1, description="Trang hiện tại (>= 1)"),
    page_size: int = Query(10, description="Số bản ghi mỗi trang (1-100)"),
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
    summary="Tải xuống tệp đính kèm",
)
def download_attachment(
    attachment_id: int,
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
)
def delete_attachment(
    attachment_id: int,
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
