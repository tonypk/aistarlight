"""Shared file-finding utilities."""

import pathlib

from fastapi import HTTPException, status

from backend.config import settings


def find_uploaded_file(file_id: str) -> tuple[str, str]:
    """Find an uploaded file by ID, returns (filepath, filename).

    Raises HTTPException if not found or invalid ID.
    """
    if not file_id.replace("-", "").isalnum():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file ID"
        )

    upload_root = pathlib.Path(settings.upload_dir).resolve()
    for ext in ("csv", "xlsx", "xls"):
        filepath = (upload_root / f"{file_id}.{ext}").resolve()
        if not str(filepath).startswith(str(upload_root)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file ID"
            )
        if filepath.exists():
            return str(filepath), f"{file_id}.{ext}"

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Uploaded file {file_id} not found",
    )
