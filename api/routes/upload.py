"""REST API endpoints for file upload."""

import logging

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from database.database import get_db
from database import crud
from services.file_service import save_upload
import pandas as pd

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["upload"])


@router.post("/upload")
async def upload_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload a CSV traffic file and create a DB record."""
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Разрешены только .csv файлы.")
    try:
        saved_name, original_name, size = await save_upload(file)
    except (ValueError, IOError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # Count rows for quick preview
    from app.config import settings
    path = settings.UPLOAD_DIR / saved_name
    try:
        df = pd.read_csv(path, nrows=0)
        row_count = sum(1 for _ in open(path, encoding="utf-8", errors="ignore")) - 1
    except Exception:
        row_count = 0

    db_file = crud.create_uploaded_file(db, saved_name, original_name, size, row_count)
    return {
        "file_id": db_file.id,
        "filename": original_name,
        "file_size": size,
        "row_count": row_count,
        "status": "uploaded",
    }
