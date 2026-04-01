"""
Conversion pipeline: validate → extract text → generate PDF.

All processing is done in memory (io.BytesIO). Nothing is written to disk.
"""
import asyncio
import io
from concurrent.futures import ThreadPoolExecutor

from fastapi.responses import StreamingResponse

from services.extractor import extract_text
from services.pdf_writer import build_pdf
from utils.file_type import detect_file_type

PROCESSING_TIMEOUT_SECONDS = 60

# Dedicated thread pool for blocking OCR/PDF work
_executor = ThreadPoolExecutor(max_workers=4)


async def convert_file(contents: bytes, content_type: str, settings: dict) -> StreamingResponse:
    file_type = detect_file_type(contents, content_type)

    loop = asyncio.get_event_loop()
    try:
        text = await asyncio.wait_for(
            loop.run_in_executor(_executor, extract_text, contents, file_type),
            timeout=PROCESSING_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        raise ValueError(
            "Processing timed out after 60 seconds. "
            "The file may be too complex. Please try a smaller or simpler file."
        )

    pdf_bytes = build_pdf(text, settings)

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="dyslexicreader_output.pdf"'},
    )
