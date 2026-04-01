"""
Upload validation: size limits and allowed MIME types.

First-pass validation uses the declared Content-Type header (fast, no file reading).
Magic-bytes validation happens in file_type.py after reading, which catches renamed files.
Page count for PDFs is enforced in the extractor to avoid opening the file twice.
"""
import os
from fastapi import UploadFile

MAX_IMAGE_BYTES = int(os.getenv("MAX_IMAGE_BYTES", str(10 * 1024 * 1024)))   # 10 MB
MAX_PDF_BYTES = int(os.getenv("MAX_PDF_BYTES", str(25 * 1024 * 1024)))        # 25 MB
MAX_PDF_PAGES = int(os.getenv("MAX_PDF_PAGES", "50"))

ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "application/pdf",
}


def validate_upload(file: UploadFile) -> str | None:
    """Return an error message string if invalid, else None."""
    content_type = file.content_type or ""

    if content_type not in ALLOWED_CONTENT_TYPES:
        return f"Unsupported file type '{content_type}'. Upload a JPG, PNG, or PDF."

    # file.size is set by python-multipart when the Content-Length header is present
    size = file.size
    if size is not None:
        if content_type == "application/pdf" and size > MAX_PDF_BYTES:
            return f"PDF exceeds the 25 MB limit ({size // (1024 * 1024)} MB uploaded)."
        if content_type.startswith("image/") and size > MAX_IMAGE_BYTES:
            return f"Image exceeds the 10 MB limit ({size // (1024 * 1024)} MB uploaded)."

    return None
