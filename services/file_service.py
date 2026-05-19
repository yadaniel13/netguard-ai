"""File upload and management service."""

import logging
import shutil
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.config import settings

logger = logging.getLogger(__name__)


async def save_upload(file: UploadFile) -> tuple[str, str, int]:
    """
    Persist the uploaded file to disk.
    Returns (saved_filename, original_filename, file_size_bytes).
    """
    suffix = Path(file.filename).suffix.lower()
    if suffix not in settings.ALLOWED_EXTENSIONS:
        raise ValueError(f"Разрешены только файлы: {settings.ALLOWED_EXTENSIONS}")

    unique_name = f"{uuid.uuid4().hex}{suffix}"
    dest = settings.UPLOAD_DIR / unique_name

    try:
        with dest.open("wb") as out:
            content = await file.read()
            out.write(content)
    except Exception as exc:
        raise IOError(f"Ошибка сохранения файла: {exc}") from exc

    size = dest.stat().st_size
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if size > max_bytes:
        dest.unlink(missing_ok=True)
        raise ValueError(f"Файл превышает максимальный размер {settings.MAX_FILE_SIZE_MB} МБ.")

    logger.info("Saved upload: %s (%d bytes)", unique_name, size)
    return unique_name, file.filename, size


def get_upload_path(filename: str) -> Path:
    return settings.UPLOAD_DIR / filename


def delete_upload(filename: str) -> None:
    path = settings.UPLOAD_DIR / filename
    path.unlink(missing_ok=True)
