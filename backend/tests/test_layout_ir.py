"""
Tests for layout-aware extraction and PDF generation.

Covers:
- Column detection: two side-by-side columns are read left-first
- Heading detection: large-font block (OCR height proxy) → HEADING
- List detection: bullet-prefixed block → LIST_ITEM
- _str_to_layout: same heading classification as legacy _is_heading
- build_pdf smoke test: DocumentLayout produces non-empty PDF bytes
"""
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from services.extractor import (
    _reconstruct_layout,
    _sort_words_by_columns,
    _is_heading_text,
    _classify_list_items_ocr,
)
from services.layout_ir import BlockKind, DocumentLayout, TextBlock
from services.pdf_writer import _is_heading, _str_to_layout, build_pdf


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_ocr_data(entries):
    """Build an image_to_data-style dict from (text, conf, block, par, line, left, top, w, h)."""
    keys = ["text", "conf", "block_num", "par_num", "line_num", "left", "top", "width", "height"]
    result = {k: [] for k in keys}
    for e in entries:
        result["text"].append(e[0])
        result["conf"].append(e[1])
        result["block_num"].append(e[2])
        result["par_num"].append(e[3])
        result["line_num"].append(e[4])
        result["left"].append(e[5])
        result["top"].append(e[6])
        result["width"].append(e[7])
        result["height"].append(e[8])
    return result


# ---------------------------------------------------------------------------
# Column detection
# ---------------------------------------------------------------------------


def test_two_columns_sorted_left_first():
    """Words in the right column (x≈500) should come after words in the left column (x≈50)."""
    # Page 700px wide; left column ~50-200, right column ~450-600 — gap of ~250px (>15%)
    image_width = 700
    words = [
        {"text": "right1", "conf": 90, "block": 1, "par": 1, "line": 1,
         "left": 450, "top": 50, "width": 60, "height": 12},
        {"text": "left1",  "conf": 90, "block": 1, "par": 1, "line": 1,
         "left": 50,  "top": 50, "width": 60, "height": 12},
        {"text": "right2", "conf": 90, "block": 1, "par": 1, "line": 2,
         "left": 450, "top": 70, "width": 60, "height": 12},
        {"text": "left2",  "conf": 90, "block": 1, "par": 1, "line": 2,
         "left": 50,  "top": 70, "width": 60, "height": 12},
    ]
    sorted_words = _sort_words_by_columns(words, image_width)
    texts = [w["text"] for w in sorted_words]
    # All left-column words must precede all right-column words
    left_indices  = [i for i, t in enumerate(texts) if t.startswith("left")]
    right_indices = [i for i, t in enumerate(texts) if t.startswith("right")]
    assert max(left_indices) < min(right_indices), (
        f"Left-column words should all precede right-column words. Got order: {texts}"
    )


def test_single_column_unchanged_order():
    """Single-column text should remain sorted top-to-bottom, left-to-right."""
    image_width = 700
    words = [
        {"text": "a", "conf": 90, "block": 1, "par": 1, "line": 1,
         "left": 50, "top": 50, "width": 20, "height": 12},
        {"text": "b", "conf": 90, "block": 1, "par": 1, "line": 1,
         "left": 80, "top": 50, "width": 20, "height": 12},
        {"text": "c", "conf": 90, "block": 1, "par": 1, "line": 2,
         "left": 50, "top": 70, "width": 20, "height": 12},
    ]
    sorted_words = _sort_words_by_columns(words, image_width)
    assert [w["text"] for w in sorted_words] == ["a", "b", "c"]


# ---------------------------------------------------------------------------
# OCR heading detection via line-height proxy
# ---------------------------------------------------------------------------


def test_large_font_block_detected_as_heading():
    """A block whose word heights are much taller than median should be classified HEADING."""
    # Median word height ≈ 10px; heading words have height ≈ 20px (ratio 2.0 > 1.6 threshold)
    data = _make_ocr_data([
        # Block 1: body text (height 10)
        ("body", 90, 1, 1, 1, 50, 100, 30, 10),
        ("text", 90, 1, 1, 1, 90, 100, 30, 10),
        # Block 2: heading (height 20)
        ("BIGHEADING", 90, 2, 1, 1, 50, 50, 80, 20),
    ])
    blocks = _reconstruct_layout(data, image_width=700)
    heading_blocks = [b for b in blocks if b.kind == BlockKind.HEADING]
    assert heading_blocks, "Expected at least one HEADING block"
    assert any("BIGHEADING" in b.text for b in heading_blocks)


def test_allcaps_single_line_detected_as_heading():
    """All-caps single-line text must be classified as a heading regardless of size."""
    data = _make_ocr_data([
        ("CHAPTER", 90, 1, 1, 1, 50, 50, 60, 12),
        ("ONE", 90, 1, 1, 1, 120, 50, 30, 12),
    ])
    blocks = _reconstruct_layout(data, image_width=700)
    assert any(b.kind == BlockKind.HEADING for b in blocks)


# ---------------------------------------------------------------------------
# List item detection
# ---------------------------------------------------------------------------


def test_bullet_char_detected_as_list_item():
    blocks = [TextBlock(kind=BlockKind.BODY, text="• First item")]
    result = _classify_list_items_ocr(blocks, image_width=700)
    assert result[0].kind == BlockKind.LIST_ITEM
    assert result[0].indent_level == 1


def test_numbered_list_detected_as_list_item():
    blocks = [TextBlock(kind=BlockKind.BODY, text="1. Do something")]
    result = _classify_list_items_ocr(blocks, image_width=700)
    assert result[0].kind == BlockKind.LIST_ITEM


def test_plain_body_not_reclassified():
    blocks = [TextBlock(kind=BlockKind.BODY, text="This is a normal paragraph.")]
    result = _classify_list_items_ocr(blocks, image_width=700)
    assert result[0].kind == BlockKind.BODY


# ---------------------------------------------------------------------------
# _str_to_layout / _is_heading parity
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("text,expected_heading", [
    ("INTRODUCTION", True),
    ("CHAPTER ONE", True),
    ("This is body text.", False),
    ("Mix Of Cases", False),
    # Multi-line is never a heading
    ("FIRST LINE\nSECOND LINE", False),
])
def test_str_to_layout_matches_is_heading(text: str, expected_heading: bool):
    """_str_to_layout must classify headings identically to the legacy _is_heading."""
    # Legacy function
    assert _is_heading(text) == expected_heading

    layout = _str_to_layout(text)
    blocks = layout.blocks
    assert blocks, f"Expected at least one block for text: {text!r}"
    if expected_heading:
        assert blocks[0].kind == BlockKind.HEADING
    else:
        assert blocks[0].kind == BlockKind.BODY


# ---------------------------------------------------------------------------
# build_pdf smoke test
# ---------------------------------------------------------------------------


def test_build_pdf_with_document_layout_returns_bytes():
    """build_pdf must return non-empty bytes for a minimal DocumentLayout."""
    layout = DocumentLayout(blocks=[
        TextBlock(kind=BlockKind.HEADING, text="TITLE", heading_level=1),
        TextBlock(kind=BlockKind.BODY, text="Some body text here."),
        TextBlock(kind=BlockKind.LIST_ITEM, text="• A list item", indent_level=1),
        TextBlock(kind=BlockKind.WHITESPACE, text=""),
        TextBlock(kind=BlockKind.BODY, text="Another paragraph."),
    ])
    settings = {"font_size": "medium", "line_spacing": "relaxed", "bg_color": "white", "font_family": "opendyslexic"}
    result = build_pdf(layout, settings)
    assert isinstance(result, bytes)
    assert len(result) > 0
    # PDF magic bytes
    assert result[:4] == b"%PDF"


def test_build_pdf_with_string_returns_bytes():
    """build_pdf must still accept a plain string for backward compatibility."""
    result = build_pdf("HEADING\n\nSome body text.", {"font_size": "medium", "line_spacing": "relaxed"})
    assert isinstance(result, bytes)
    assert result[:4] == b"%PDF"
