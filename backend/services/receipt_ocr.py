"""HTTP client for the PaddleOCR microservice."""

import logging
from pathlib import Path

import httpx

from backend.config import settings

logger = logging.getLogger(__name__)

OCR_TIMEOUT = 60.0  # seconds


async def ocr_image(file_path: str) -> dict:
    """Send an image to the OCR microservice and return extracted text.

    Args:
        file_path: Path to the image file on disk.

    Returns:
        dict with keys: text (str), lines (list[dict]), line_count (int).

    Raises:
        RuntimeError: If the OCR service is unreachable or returns an error.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {file_path}")

    url = f"{settings.ocr_service_url}/ocr"

    async with httpx.AsyncClient(timeout=OCR_TIMEOUT) as client:
        with open(file_path, "rb") as f:
            files = {"file": (path.name, f, _guess_mime(path.suffix))}
            response = await client.post(url, files=files)

    if response.status_code != 200:
        detail = response.text[:200]
        logger.error("OCR service returned %d: %s", response.status_code, detail)
        raise RuntimeError(f"OCR service error ({response.status_code}): {detail}")

    data = response.json()
    logger.info("OCR: %d lines from %s", data.get("line_count", 0), path.name)
    return data


def _guess_mime(suffix: str) -> str:
    return {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".bmp": "image/bmp",
        ".tiff": "image/tiff",
        ".tif": "image/tiff",
        ".webp": "image/webp",
    }.get(suffix.lower(), "application/octet-stream")
