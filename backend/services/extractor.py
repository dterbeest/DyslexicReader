"""
Text extraction: branches on file type.

- image (jpg/png): preprocess → pytesseract OCR
- digital PDF (embedded text): pdfplumber
- scanned PDF (image-only pages): pdf2image → preprocess → pytesseract
- mixed PDF: per-page handling
"""
import io
import logging
import re

import pytesseract
from pytesseract import Output
import pdfplumber
from PIL import Image, ImageOps
from pdf2image import convert_from_bytes

from utils.image_processing import preprocess_image

logger = logging.getLogger(__name__)

# Minimum number of non-whitespace characters to consider OCR successful.
_MIN_TEXT_LENGTH = 10
MAX_PDF_PAGES = 50


def extract_text(contents: bytes, file_type: str, lang: str = "eng") -> str:
    if file_type == "image":
        return _ocr_image_bytes(contents, lang)
    if file_type == "pdf":
        return _extract_pdf(contents, lang)
    raise ValueError(f"Unsupported file type: {file_type}")


def _ocr_image_bytes(contents: bytes, lang: str) -> str:
    image = Image.open(io.BytesIO(contents))
    image = ImageOps.exif_transpose(image)
    image = preprocess_image(image)
    return _run_ocr(image, lang)


def _run_ocr(image: Image.Image, lang: str = "eng") -> str:
    data = pytesseract.image_to_data(image, lang=lang, output_type=Output.DICT)
    _log_confidence(data)
    text = _reconstruct_paragraphs(data)
    text = _clean_text(text)
    if len(text.replace(" ", "")) < _MIN_TEXT_LENGTH:
        raise ValueError("OCR produced no usable text. The image may be blank or too low quality.")
    return text


def _reconstruct_paragraphs(data: dict) -> str:
    """
    Rebuild text from pytesseract word-level data, inserting paragraph breaks
    when the block or paragraph number changes.
    """
    paragraphs: list[str] = []
    current_lines: list[str] = []
    current_line_words: list[str] = []
    prev_block = None
    prev_par = None
    prev_line = None

    n = len(data["text"])
    for i in range(n):
        word = data["text"][i]
        conf = data["conf"][i]
        block = data["block_num"][i]
        par = data["par_num"][i]
        line = data["line_num"][i]

        # Skip empty tokens or very low confidence detections
        if not word.strip() or conf == -1:
            continue

        # Detect paragraph boundary
        if prev_block is not None and (block != prev_block or par != prev_par):
            if current_line_words:
                current_lines.append(" ".join(current_line_words))
                current_line_words = []
            if current_lines:
                paragraphs.append("\n".join(current_lines))
                current_lines = []
        elif prev_line is not None and line != prev_line:
            # New line within same paragraph
            if current_line_words:
                current_lines.append(" ".join(current_line_words))
                current_line_words = []

        current_line_words.append(word)
        prev_block = block
        prev_par = par
        prev_line = line

    # Flush remaining
    if current_line_words:
        current_lines.append(" ".join(current_line_words))
    if current_lines:
        paragraphs.append("\n".join(current_lines))

    return "\n\n".join(paragraphs)


def _clean_text(text: str) -> str:
    """Strip non-printable characters and normalize whitespace."""
    # Remove non-printable characters (keep newlines and tabs)
    text = re.sub(r"[^\x09\x0a\x0d\x20-\x7e\u00a0-\ufffd]", "", text)
    # Collapse runs of spaces/tabs within lines
    text = re.sub(r"[ \t]+", " ", text)
    # Normalize line endings and collapse 3+ newlines to double
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _log_confidence(data: dict) -> None:
    confidences = [c for c in data["conf"] if c != -1]
    if confidences:
        avg_conf = sum(confidences) / len(confidences)
        logger.debug("OCR confidence: %.1f%% (words: %d)", avg_conf, len(confidences))


def _extract_pdf(contents: bytes, lang: str = "eng") -> str:
    try:
        with pdfplumber.open(io.BytesIO(contents)) as pdf:
            if len(pdf.pages) > MAX_PDF_PAGES:
                raise ValueError(
                    f"PDF exceeds the {MAX_PDF_PAGES}-page limit ({len(pdf.pages)} pages). "
                    "Please split the document and re-upload."
                )

            pages_text: list[str] = []
            for page in pdf.pages:
                text = page.extract_text()
                if text and text.strip():
                    pages_text.append(text.strip())
                else:
                    # Scanned page — rasterize and OCR
                    page_image = _rasterize_page(contents, page.page_number)
                    pages_text.append(_run_ocr(page_image, lang))

    except Exception as exc:
        # pdfplumber/pdfminer raises various exceptions for encrypted PDFs
        msg = str(exc).lower()
        if "encrypt" in msg or "password" in msg or "decrypt" in msg:
            raise ValueError(
                "This PDF is password-protected. Please remove the password and try again."
            ) from exc
        raise

    return "\n\n".join(pages_text)


def _rasterize_page(contents: bytes, page_number: int) -> Image.Image:
    images = convert_from_bytes(contents, first_page=page_number, last_page=page_number, dpi=300)
    image = images[0]
    return preprocess_image(image)
