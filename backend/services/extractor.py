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
import statistics
import unicodedata

import pytesseract
from pytesseract import Output
import pdfplumber
from PIL import Image, ImageOps
from pdf2image import convert_from_bytes

from utils.image_processing import preprocess_image
from services.layout_ir import BlockKind, DocumentLayout, TextBlock

logger = logging.getLogger(__name__)

# Minimum number of non-whitespace characters to consider OCR successful.
_MIN_TEXT_LENGTH = 10
MAX_PDF_PAGES = 50

_TESS_CONFIG = "--oem 3 --psm 3"
# Minimum extracted words from pdfplumber to trust digital text over OCR.
_MIN_DIGITAL_WORDS = 20

# Column detection: a gap spanning more than this fraction of page width
# between occupied x-regions is treated as a column boundary.
_COLUMN_GAP_FRACTION = 0.15

# Heading detection thresholds (relative to median body font size / line height)
_HEADING_SIZE_RATIO_H1 = 1.6
_HEADING_SIZE_RATIO_H2 = 1.25

# OCR heading: line bbox height > this multiple of median word height
_OCR_HEADING_HEIGHT_RATIO = 1.4

# List detection: left-indent more than this fraction of page width vs. body
_OCR_LIST_INDENT_FRACTION = 0.10

# Bullet / list-prefix patterns
_BULLET_CHARS = {"•", "·", "‣", "◦", "–", "—", "*", "-"}
_LIST_PREFIX_RE = re.compile(r"^\s*(\d+[\.\)]\s|\([a-z]\)\s|[a-z][\.\)]\s)", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def extract_text(contents: bytes, file_type: str, lang: str = "eng") -> str:
    """Return extracted text as a plain string (legacy / test path)."""
    if file_type == "image":
        return _ocr_image_bytes(contents, lang)
    if file_type == "pdf":
        return _extract_pdf(contents, lang)
    raise ValueError(f"Unsupported file type: {file_type}")


def extract_layout(contents: bytes, file_type: str, lang: str = "eng") -> DocumentLayout:
    """Return structured DocumentLayout preserving reading order and block types."""
    if file_type == "image":
        return _ocr_image_layout(contents, lang)
    if file_type == "pdf":
        return _extract_pdf_layout(contents, lang)
    raise ValueError(f"Unsupported file type: {file_type}")


# ---------------------------------------------------------------------------
# Image / OCR paths
# ---------------------------------------------------------------------------


def _ocr_image_bytes(contents: bytes, lang: str) -> str:
    image = Image.open(io.BytesIO(contents))
    image = ImageOps.exif_transpose(image)
    image = preprocess_image(image)
    return _run_ocr(image, lang)


def _ocr_image_layout(contents: bytes, lang: str) -> DocumentLayout:
    image = Image.open(io.BytesIO(contents))
    image = ImageOps.exif_transpose(image)
    image = preprocess_image(image)
    return _run_ocr_layout(image, lang)


def _run_ocr(image: Image.Image, lang: str = "eng") -> str:
    data = pytesseract.image_to_data(image, lang=lang, output_type=Output.DICT,
                                     config=_TESS_CONFIG)
    _log_confidence(data)
    text = _reconstruct_paragraphs(data)
    text = _clean_text(text)
    if len(text.replace(" ", "")) < _MIN_TEXT_LENGTH:
        raise ValueError("OCR produced no usable text. The image may be blank or too low quality.")
    return text


def _run_ocr_layout(image: Image.Image, lang: str = "eng") -> DocumentLayout:
    data = pytesseract.image_to_data(image, lang=lang, output_type=Output.DICT,
                                     config=_TESS_CONFIG)
    _log_confidence(data)
    image_width = image.width
    blocks = _reconstruct_layout(data, image_width)
    blocks = _classify_list_items_ocr(blocks, image_width)
    flat_text = " ".join(b.text for b in blocks if b.kind != BlockKind.WHITESPACE)
    if len(flat_text.replace(" ", "")) < _MIN_TEXT_LENGTH:
        raise ValueError("OCR produced no usable text. The image may be blank or too low quality.")
    return DocumentLayout(blocks=blocks)


# ---------------------------------------------------------------------------
# OCR paragraph reconstruction (legacy — kept for existing tests)
# ---------------------------------------------------------------------------


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

        # Skip empty tokens or Tesseract layout markers (conf == -1)
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


# ---------------------------------------------------------------------------
# OCR layout reconstruction (layout-aware)
# ---------------------------------------------------------------------------


def _reconstruct_layout(data: dict, image_width: int) -> list[TextBlock]:
    """
    Rebuild structured TextBlocks from pytesseract word-level data.

    Uses bounding-box data (left, top, width, height) when available to detect
    columns and sort words in the correct reading order before grouping into
    paragraphs. Falls back to structural (block/par/line) grouping when bbox
    data is absent (e.g., in unit tests).
    """
    has_bbox = "left" in data and "top" in data

    n = len(data["text"])

    # Collect valid words with all metadata
    words = []
    for i in range(n):
        word = data["text"][i]
        conf = data["conf"][i]
        if not word.strip() or conf == -1:
            continue
        entry = {
            "text": word,
            "conf": conf,
            "block": data["block_num"][i],
            "par": data["par_num"][i],
            "line": data["line_num"][i],
        }
        if has_bbox:
            entry["left"] = data["left"][i]
            entry["top"] = data["top"][i]
            entry["width"] = data["width"][i]
            entry["height"] = data["height"][i]
        words.append(entry)

    if not words:
        return []

    if has_bbox:
        words = _sort_words_by_columns(words, image_width)

    # Group into paragraphs using block/par boundaries (structural grouping)
    return _group_words_into_blocks(words, has_bbox)


def _sort_words_by_columns(words: list[dict], image_width: int) -> list[dict]:
    """
    Re-order words so multi-column text is read left-column-first.

    Detects column boundaries by finding horizontal gaps in word x-positions
    wider than _COLUMN_GAP_FRACTION of the image width.
    """
    if image_width <= 0 or not words:
        return words

    left_positions = [w["left"] for w in words]
    gap_threshold = _COLUMN_GAP_FRACTION * image_width

    # Build a simple coverage map: which x-positions are occupied?
    # Use bins of ~5px wide.
    bin_size = max(1, image_width // 200)
    occupied = set()
    for w in words:
        x_start = w["left"] // bin_size
        x_end = (w["left"] + w["width"]) // bin_size
        for b in range(x_start, x_end + 1):
            occupied.add(b)

    # Find column boundaries: gaps in occupied bins wider than threshold
    max_bin = max(w["left"] + w["width"] for w in words) // bin_size
    gap_bins = int(gap_threshold / bin_size)

    column_boundaries = [0]  # x-pixel positions where each column starts
    gap_start = None
    for b in range(max_bin + 1):
        if b not in occupied:
            if gap_start is None:
                gap_start = b
        else:
            if gap_start is not None:
                gap_len = b - gap_start
                if gap_len >= gap_bins:
                    # This is a column boundary; the new column starts at b * bin_size
                    boundary_x = b * bin_size
                    # Only treat as column boundary if it's not at the very edges
                    if boundary_x > image_width * 0.1 and boundary_x < image_width * 0.9:
                        column_boundaries.append(boundary_x)
                gap_start = None

    if len(column_boundaries) == 1:
        # Single column — sort by (top, left)
        return sorted(words, key=lambda w: (w["top"], w["left"]))

    # Assign each word to a column (index of the last boundary <= word's left)
    def column_index(word):
        col = 0
        for idx, boundary in enumerate(column_boundaries):
            if word["left"] >= boundary:
                col = idx
        return col

    # Sort: column first, then top within column, then left within line
    return sorted(words, key=lambda w: (column_index(w), w["top"], w["left"]))


def _group_words_into_blocks(words: list[dict], has_bbox: bool) -> list[TextBlock]:
    """
    Group sorted words into TextBlocks using structural (block/par) transitions.
    Detect headings using line-height proxy when bbox data is available.
    """
    if not words:
        return []

    # Compute median word height for heading detection
    median_height = None
    if has_bbox:
        heights = [w["height"] for w in words if w["height"] > 0]
        if heights:
            median_height = statistics.median(heights)

    blocks: list[TextBlock] = []
    current_lines: list[str] = []
    current_line_words: list[str] = []
    current_line_heights: list[int] = []
    prev_block = None
    prev_par = None
    prev_line = None

    def flush_paragraph():
        if current_line_words:
            current_lines.append(" ".join(current_line_words))
        if current_lines:
            para_text = _clean_text("\n".join(current_lines))
            if para_text:
                kind, heading_level = _classify_block_kind(
                    para_text, current_line_heights, median_height
                )
                blocks.append(TextBlock(kind=kind, text=para_text, heading_level=heading_level))
        current_lines.clear()
        current_line_words.clear()
        current_line_heights.clear()

    for word in words:
        block = word["block"]
        par = word["par"]
        line = word["line"]

        if prev_block is not None and (block != prev_block or par != prev_par):
            flush_paragraph()
        elif prev_line is not None and line != prev_line:
            if current_line_words:
                current_lines.append(" ".join(current_line_words))
                current_line_words.clear()
                current_line_heights.clear()

        current_line_words.append(word["text"])
        if has_bbox and word["height"] > 0:
            current_line_heights.append(word["height"])
        prev_block = block
        prev_par = par
        prev_line = line

    flush_paragraph()
    return blocks


def _classify_block_kind(
    text: str,
    line_heights: list[int],
    median_height: float | None,
) -> tuple[BlockKind, int]:
    """Return (BlockKind, heading_level) for a block of text."""
    # All-caps single-line heuristic (always applies)
    if _is_heading_text(text):
        return BlockKind.HEADING, 1

    # Line-height proxy for headings (OCR path)
    if median_height and line_heights:
        block_median_h = statistics.median(line_heights)
        if block_median_h > median_height * _HEADING_SIZE_RATIO_H1:
            return BlockKind.HEADING, 1
        if block_median_h > median_height * _HEADING_SIZE_RATIO_H2:
            return BlockKind.HEADING, 2

    return BlockKind.BODY, 1


def _classify_list_items_ocr(blocks: list[TextBlock], image_width: int) -> list[TextBlock]:
    """Post-processing pass: reclassify BODY blocks that look like list items."""
    for block in blocks:
        if block.kind != BlockKind.BODY:
            continue
        text = block.text.strip()
        if not text:
            continue
        first_char = text[0]
        if first_char in _BULLET_CHARS or _LIST_PREFIX_RE.match(text):
            block.kind = BlockKind.LIST_ITEM
            block.indent_level = 1
    return blocks


# ---------------------------------------------------------------------------
# PDF extraction paths
# ---------------------------------------------------------------------------


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
                if text and len(text.split()) >= _MIN_DIGITAL_WORDS:
                    pages_text.append(text.strip())
                else:
                    page_image = _rasterize_page(contents, page.page_number)
                    pages_text.append(_run_ocr(page_image, lang))

    except Exception as exc:
        msg = str(exc).lower()
        if "encrypt" in msg or "password" in msg or "decrypt" in msg:
            raise ValueError(
                "This PDF is password-protected. Please remove the password and try again."
            ) from exc
        raise

    return "\n\n".join(pages_text)


def _extract_pdf_layout(contents: bytes, lang: str = "eng") -> DocumentLayout:
    all_blocks: list[TextBlock] = []

    try:
        with pdfplumber.open(io.BytesIO(contents)) as pdf:
            if len(pdf.pages) > MAX_PDF_PAGES:
                raise ValueError(
                    f"PDF exceeds the {MAX_PDF_PAGES}-page limit ({len(pdf.pages)} pages). "
                    "Please split the document and re-upload."
                )

            for page in pdf.pages:
                text = page.extract_text()
                if text and len(text.split()) >= _MIN_DIGITAL_WORDS:
                    page_blocks = _extract_digital_page(page)
                else:
                    page_image = _rasterize_page(contents, page.page_number)
                    page_blocks = _run_ocr_layout(page_image, lang).blocks

                if all_blocks and page_blocks:
                    # Insert a whitespace sentinel between pages
                    all_blocks.append(TextBlock(kind=BlockKind.WHITESPACE, text=""))
                all_blocks.extend(page_blocks)

    except Exception as exc:
        msg = str(exc).lower()
        if "encrypt" in msg or "password" in msg or "decrypt" in msg:
            raise ValueError(
                "This PDF is password-protected. Please remove the password and try again."
            ) from exc
        raise

    return DocumentLayout(blocks=all_blocks)


def _extract_digital_page(page) -> list[TextBlock]:
    """
    Extract structured TextBlocks from a pdfplumber page with embedded text.

    Uses word bboxes for column detection and char font-sizes for heading
    classification.
    """
    words = page.extract_words()
    if not words:
        return []

    page_width = float(page.width)

    # Compute median body font size from page chars
    char_sizes = [c["size"] for c in (page.chars or []) if c.get("size", 0) > 0]
    median_font_size = statistics.median(char_sizes) if char_sizes else None

    # Detect columns and sort words into reading order
    words = _sort_pdf_words_by_columns(words, page_width)

    # Group words into line-then-paragraph clusters
    raw_paragraphs = _group_pdf_words_into_paragraphs(words)

    blocks: list[TextBlock] = []
    for para_words in raw_paragraphs:
        if not para_words:
            continue
        # Gather text
        text = _clean_text(" ".join(w["text"] for w in para_words))
        if not text:
            continue

        # Compute median font size for this block's characters
        block_font_size = _median_font_size_for_words(para_words, page)

        kind, heading_level = _classify_digital_block(text, block_font_size, median_font_size)
        blocks.append(TextBlock(kind=kind, text=text, heading_level=heading_level))

    # Post-process: detect list items
    blocks = _classify_list_items_digital(blocks, page)

    return blocks


def _sort_pdf_words_by_columns(words: list[dict], page_width: float) -> list[dict]:
    """Re-order pdfplumber words for correct column reading order."""
    if not words or page_width <= 0:
        return words

    gap_threshold = _COLUMN_GAP_FRACTION * page_width
    bin_size = max(1.0, page_width / 200)

    occupied: set[int] = set()
    for w in words:
        x0 = float(w["x0"])
        x1 = float(w["x1"])
        b_start = int(x0 / bin_size)
        b_end = int(x1 / bin_size)
        for b in range(b_start, b_end + 1):
            occupied.add(b)

    max_bin = int(max(float(w["x1"]) for w in words) / bin_size)
    gap_bins = max(1, int(gap_threshold / bin_size))

    column_boundaries = [0.0]
    gap_start = None
    for b in range(max_bin + 1):
        if b not in occupied:
            if gap_start is None:
                gap_start = b
        else:
            if gap_start is not None:
                gap_len = b - gap_start
                if gap_len >= gap_bins:
                    boundary_x = b * bin_size
                    if boundary_x > page_width * 0.1 and boundary_x < page_width * 0.9:
                        column_boundaries.append(boundary_x)
                gap_start = None

    if len(column_boundaries) == 1:
        return sorted(words, key=lambda w: (float(w["top"]), float(w["x0"])))

    def col_index(word):
        col = 0
        for idx, boundary in enumerate(column_boundaries):
            if float(word["x0"]) >= boundary:
                col = idx
        return col

    return sorted(words, key=lambda w: (col_index(w), float(w["top"]), float(w["x0"])))


def _group_pdf_words_into_paragraphs(words: list[dict]) -> list[list[dict]]:
    """
    Group sorted pdfplumber words into paragraphs.

    A new paragraph begins when the vertical gap between consecutive lines
    exceeds 1.5× the median line height.
    """
    if not words:
        return []

    # Cluster words into lines by proximity of their top coordinate
    lines: list[list[dict]] = []
    current_line: list[dict] = [words[0]]
    line_top_tolerance = 3.0  # points; words within this vertical range are on the same line

    for word in words[1:]:
        prev_top = float(current_line[-1]["top"])
        cur_top = float(word["top"])
        if abs(cur_top - prev_top) <= line_top_tolerance:
            current_line.append(word)
        else:
            lines.append(current_line)
            current_line = [word]
    if current_line:
        lines.append(current_line)

    if not lines:
        return []

    # Compute median line height
    line_tops = [float(line[0]["top"]) for line in lines]
    if len(line_tops) >= 2:
        gaps = [line_tops[i + 1] - line_tops[i] for i in range(len(line_tops) - 1)]
        positive_gaps = [g for g in gaps if g > 0]
        median_gap = statistics.median(positive_gaps) if positive_gaps else 12.0
    else:
        median_gap = 12.0

    para_gap_threshold = median_gap * 1.5

    # Group lines into paragraphs
    paragraphs: list[list[dict]] = []
    current_para: list[dict] = list(lines[0])
    prev_top = float(lines[0][0]["top"])

    for line in lines[1:]:
        cur_top = float(line[0]["top"])
        if cur_top - prev_top > para_gap_threshold:
            paragraphs.append(current_para)
            current_para = list(line)
        else:
            current_para.extend(line)
        prev_top = cur_top

    if current_para:
        paragraphs.append(current_para)

    return paragraphs


def _median_font_size_for_words(para_words: list[dict], page) -> float | None:
    """Estimate median font size for a set of words using pdfplumber char data."""
    if not page.chars:
        return None

    # Build a set of approximate word x0 positions for matching
    word_x0s = {round(float(w["x0"]), 1) for w in para_words}
    word_tops = {round(float(w["top"]), 1) for w in para_words}

    sizes = []
    for char in page.chars:
        cx = round(float(char.get("x0", 0)), 1)
        ct = round(float(char.get("top", 0)), 1)
        size = char.get("size", 0)
        if size > 0 and cx in word_x0s and ct in word_tops:
            sizes.append(size)

    return statistics.median(sizes) if sizes else None


def _classify_digital_block(
    text: str,
    block_font_size: float | None,
    page_median_font_size: float | None,
) -> tuple[BlockKind, int]:
    """Classify a pdfplumber text block as heading or body."""
    # All-caps heuristic (fallback / reinforcement)
    if _is_heading_text(text):
        return BlockKind.HEADING, 1

    if block_font_size and page_median_font_size and page_median_font_size > 0:
        ratio = block_font_size / page_median_font_size
        if ratio >= _HEADING_SIZE_RATIO_H1:
            return BlockKind.HEADING, 1
        if ratio >= _HEADING_SIZE_RATIO_H2:
            return BlockKind.HEADING, 2

    return BlockKind.BODY, 1


def _classify_list_items_digital(blocks: list[TextBlock], page) -> list[TextBlock]:
    """Reclassify BODY blocks that look like list items (digital PDF path)."""
    # Check pdfplumber chars for Unicode bullet characters at start of block
    bullet_x0s: set[float] = set()
    if page.chars:
        for char in page.chars:
            if char.get("text") in _BULLET_CHARS:
                bullet_x0s.add(round(float(char.get("x0", -1)), 0))

    for block in blocks:
        if block.kind != BlockKind.BODY:
            continue
        text = block.text.strip()
        if not text:
            continue
        if text[0] in _BULLET_CHARS or _LIST_PREFIX_RE.match(text):
            block.kind = BlockKind.LIST_ITEM
            block.indent_level = 1
    return blocks


# ---------------------------------------------------------------------------
# Shared utilities
# ---------------------------------------------------------------------------


def _is_heading_text(text: str) -> bool:
    """True for a single all-caps line of ≤80 characters."""
    lines = text.strip().splitlines()
    if len(lines) != 1:
        return False
    line = lines[0].strip()
    letters = re.sub(r"[^a-zA-Z]", "", line)
    return bool(letters) and letters == letters.upper() and len(line) <= 80


def _clean_text(text: str) -> str:
    """Strip non-printable characters and normalize whitespace."""
    # Normalize Unicode ligatures (ﬁ→fi, ﬂ→fl, ﬀ→ff, etc.)
    text = unicodedata.normalize("NFKD", text)
    # Remove non-printable characters (keep newlines and tabs)
    text = re.sub(r"[^\x09\x0a\x0d\x20-\x7e\u00a0-\ufffd]", "", text)
    # Rejoin words hyphenated across line breaks (e.g. "some-\nword" → "someword")
    text = re.sub(r"-\n(?=[a-z])", "", text)
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


def _rasterize_page(contents: bytes, page_number: int) -> Image.Image:
    images = convert_from_bytes(contents, first_page=page_number, last_page=page_number, dpi=300)
    image = images[0]
    return preprocess_image(image)
