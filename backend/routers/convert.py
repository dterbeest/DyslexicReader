import logging
import os

from fastapi import APIRouter, Request, UploadFile, File, Form
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from services.converter import convert_file
from utils.validation import validate_upload

RATE_LIMIT = os.getenv("RATE_LIMIT", "10/hour")

limiter = Limiter(key_func=get_remote_address)
router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/convert")
@limiter.limit(RATE_LIMIT)
async def convert(
    request: Request,
    file: UploadFile = File(...),
    font_size: str = Form("medium"),
    line_spacing: str = Form("relaxed"),
    bg_color: str = Form("white"),
    language: str = Form("eng"),
):
    error = validate_upload(file)
    if error:
        return JSONResponse(status_code=400, content={"error": error})
<<<<<<< feature/dutch-language-support

    if language not in ("eng", "nld"):
        return JSONResponse(status_code=400, content={"error": "Unsupported language."})
=======
>>>>>>> main

    contents = await file.read()

    # Re-check size after reading (Content-Length may be absent)
    if file.content_type == "application/pdf" and len(contents) > 25 * 1024 * 1024:
        return JSONResponse(status_code=400, content={"error": "PDF exceeds the 25 MB limit."})
    if (file.content_type or "").startswith("image/") and len(contents) > 10 * 1024 * 1024:
        return JSONResponse(status_code=400, content={"error": "Image exceeds the 10 MB limit."})

    settings = {
        "font_size": font_size,
        "line_spacing": line_spacing,
        "bg_color": bg_color,
        "language": language,
    }

    try:
        return await convert_file(contents, file.content_type or "", settings)
    except ValueError as exc:
        msg = str(exc)
        if "no usable text" in msg.lower():
            return JSONResponse(status_code=422, content={"error": msg})
        return JSONResponse(status_code=400, content={"error": msg})
    except Exception:
        logger.exception("Unexpected error during conversion")
        return JSONResponse(
            status_code=500,
            content={"error": "An unexpected error occurred. Please try again."},
        )
