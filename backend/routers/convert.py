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


@router.post("/convert")
@limiter.limit(RATE_LIMIT)
async def convert(
    request: Request,
    file: UploadFile = File(...),
    font_size: str = Form("medium"),
    line_spacing: str = Form("relaxed"),
    bg_color: str = Form("white"),
):
    error = validate_upload(file)
    if error:
        return JSONResponse(status_code=422, content={"detail": error})

    contents = await file.read()

    settings = {
        "font_size": font_size,
        "line_spacing": line_spacing,
        "bg_color": bg_color,
    }

    return await convert_file(contents, file.content_type or "", settings)
