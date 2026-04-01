"""
Detect file type from magic bytes, not file extension or Content-Type header.
"""
import magic

ALLOWED_MIME_TYPES = {
    "image/jpeg": "image",
    "image/png": "image",
    "application/pdf": "pdf",
}


def detect_file_type(contents: bytes, declared_content_type: str = "") -> str:
    mime = magic.from_buffer(contents, mime=True)
    file_type = ALLOWED_MIME_TYPES.get(mime)
    if file_type is None:
        raise ValueError(f"Unsupported file type: {mime}")
    return file_type
