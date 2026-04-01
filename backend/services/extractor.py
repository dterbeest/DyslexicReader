"""
Text extraction: branches on file type.

- image (jpg/png): preprocess → pytesseract OCR
- digital PDF (embedded text): pdfplumber
- scanned PDF (image-only pages): pdf2image → preprocess → pytesseract
- mixed PDF: per-page handling
"""
import io

import pytesseract
import pdfplumber
from PIL import Image
from pdf2image import convert_from_bytes

from utils.image_processing import preprocess_image


def extract_text(contents: bytes, file_type: str) -> str:
    if file_type == "image":
        return _ocr_image_bytes(contents)
    if file_type == "pdf":
        return _extract_pdf(contents)
    raise ValueError(f"Unsupported file type: {file_type}")


def _ocr_image_bytes(contents: bytes) -> str:
    image = Image.open(io.BytesIO(contents))
    image = preprocess_image(image)
    return pytesseract.image_to_string(image, lang="eng")


def _extract_pdf(contents: bytes) -> str:
    pages_text: list[str] = []

    with pdfplumber.open(io.BytesIO(contents)) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text and text.strip():
                pages_text.append(text.strip())
            else:
                # Scanned page — rasterize and OCR
                page_image = _rasterize_page(contents, page.page_number)
                pages_text.append(pytesseract.image_to_string(page_image, lang="eng"))

    return "\n\n".join(pages_text)


def _rasterize_page(contents: bytes, page_number: int) -> Image.Image:
    images = convert_from_bytes(contents, first_page=page_number, last_page=page_number, dpi=300)
    image = images[0]
    return preprocess_image(image)
