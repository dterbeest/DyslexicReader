"""
Conversion pipeline: validate → extract text → generate PDF.

All processing is done in memory (io.BytesIO). Nothing is written to disk.
"""
import io

from fastapi.responses import StreamingResponse

from services.extractor import extract_text
from services.pdf_writer import build_pdf
from utils.file_type import detect_file_type


async def convert_file(contents: bytes, content_type: str, settings: dict) -> StreamingResponse:
    file_type = detect_file_type(contents, content_type)
    text = extract_text(contents, file_type)
    pdf_bytes = build_pdf(text, settings)

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="result.pdf"'},
    )
