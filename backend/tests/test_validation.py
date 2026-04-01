from unittest.mock import MagicMock
from utils.validation import validate_upload, MAX_IMAGE_BYTES, MAX_PDF_BYTES


def _mock_upload(content_type: str, size: int | None = None) -> MagicMock:
    f = MagicMock()
    f.content_type = content_type
    f.size = size
    return f


def test_valid_jpeg():
    assert validate_upload(_mock_upload("image/jpeg", 1024)) is None


def test_valid_png():
    assert validate_upload(_mock_upload("image/png", 1024)) is None


def test_valid_pdf():
    assert validate_upload(_mock_upload("application/pdf", 1024)) is None


def test_unsupported_type():
    error = validate_upload(_mock_upload("application/msword"))
    assert error is not None
    assert "Unsupported" in error


def test_image_too_large():
    error = validate_upload(_mock_upload("image/jpeg", MAX_IMAGE_BYTES + 1))
    assert error is not None
    assert "10 MB" in error


def test_pdf_too_large():
    error = validate_upload(_mock_upload("application/pdf", MAX_PDF_BYTES + 1))
    assert error is not None
    assert "25 MB" in error
