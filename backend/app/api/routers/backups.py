"""
Backup router: create, list, download, upload, restore, and delete database backups.

Endpoints:
  GET    /api/backups/                    — list all backups
  POST   /api/backups/                    — create new backup (pg_dump)
  GET    /api/backups/{filename}/download — download a backup ZIP
  POST   /api/backups/upload             — upload a backup ZIP
  POST   /api/backups/{filename}/restore — restore database from backup
  DELETE /api/backups/{filename}         — delete a backup
"""
import logging
from fastapi import APIRouter, Depends, Request, UploadFile, File, HTTPException, status
from fastapi.responses import FileResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.api.schemas import BackupItem, BackupList
from app.api.services import backup_service
from app.dependencies.auth import require_auth
from app.dependencies.db_session import get_dbsession

limiter = Limiter(key_func=get_remote_address)
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/backups", tags=["backups"])

MAX_UPLOAD_BYTES = 500 * 1024 * 1024  # 500 MB


@router.get("/", response_model=BackupList)
@limiter.limit("30/minute")
def list_backups(request: Request, _user=Depends(require_auth)):
    backups = backup_service.list_backups()
    return BackupList(backups=backups, total=len(backups))


@router.post("/", response_model=BackupItem, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def create_backup(request: Request, _user=Depends(require_auth)):
    return backup_service.create_backup()


@router.post("/upload", response_model=BackupItem, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def upload_backup(
    request: Request,
    file: UploadFile = File(...),
    _user=Depends(require_auth),
):
    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Backup file must be 500 MB or smaller.",
        )
    filename = file.filename or ""
    return backup_service.save_uploaded_backup(filename, data)


@router.get("/{filename}/download")
@limiter.limit("10/minute")
def download_backup(filename: str, request: Request, _user=Depends(require_auth)):
    path = backup_service.get_backup_path(filename)
    return FileResponse(
        path=str(path),
        media_type="application/octet-stream",
        filename=filename,
    )


@router.post("/{filename}/restore", status_code=status.HTTP_200_OK)
@limiter.limit("3/minute")
def restore_backup(
    filename: str,
    request: Request,
    db: Session = Depends(get_dbsession),
    _user=Depends(require_auth),
):
    # Return this request's DB connection to the pool before restore begins.
    # restore_backup calls engine.dispose() to close the pool, then
    # pg_terminate_backend to kill any remaining connections. Without this,
    # pg_terminate_backend kills the active session connection and FastAPI's
    # cleanup (db.close() in get_dbsession) crashes on the dead connection.
    # FastAPI caches dependencies per-request, so this is the same Session
    # instance that require_auth used — closing it here is safe and idempotent.
    db.close()
    backup_service.restore_backup(filename)
    return {"status": "restored", "filename": filename}


@router.delete("/{filename}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
def delete_backup(filename: str, request: Request, _user=Depends(require_auth)):
    backup_service.delete_backup(filename)
