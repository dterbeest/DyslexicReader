"""
Tests for OCR text extraction helpers in services/extractor.py.

These tests use mocked pytesseract responses so no Tesseract binary is required
in the test environment.
"""
from unittest.mock import patch, MagicMock

import pytest
from PIL import Image

from services.extractor import (
    _clean_text,
    _reconstruct_paragraphs,
    _run_ocr,
)


# ---------------------------------------------------------------------------
# _clean_text
# ---------------------------------------------------------------------------


def test_clean_text_strips_non_printable():
    assert _clean_text("hello\x00world") == "helloworld"


def test_clean_text_collapses_spaces():
    assert _clean_text("hello   world") == "hello world"


def test_clean_text_normalizes_paragraph_breaks():
    text = "para one\n\n\n\npara two"
    assert _clean_text(text) == "para one\n\npara two"


def test_clean_text_strips_surrounding_whitespace():
    assert _clean_text("  hello  ") == "hello"


def test_clean_text_preserves_single_newlines():
    assert _clean_text("line one\nline two") == "line one\nline two"


def test_clean_text_converts_crlf():
    assert _clean_text("line one\r\nline two") == "line one\nline two"


# ---------------------------------------------------------------------------
# _reconstruct_paragraphs
# ---------------------------------------------------------------------------


def _make_data(entries):
    """Build an image_to_data-style dict from a list of (text, conf, block, par, line)."""
    return {
        "text": [e[0] for e in entries],
        "conf": [e[1] for e in entries],
        "block_num": [e[2] for e in entries],
        "par_num": [e[3] for e in entries],
        "line_num": [e[4] for e in entries],
    }


def test_reconstruct_single_paragraph():
    data = _make_data([
        ("Hello", 95, 1, 1, 1),
        ("world", 90, 1, 1, 1),
    ])
    assert _reconstruct_paragraphs(data) == "Hello world"


def test_reconstruct_two_paragraphs():
    data = _make_data([
        ("First", 90, 1, 1, 1),
        ("para", 90, 1, 1, 1),
        ("Second", 85, 2, 1, 1),
        ("para", 85, 2, 1, 1),
    ])
    result = _reconstruct_paragraphs(data)
    assert result == "First para\n\nSecond para"


def test_reconstruct_preserves_line_breaks_within_paragraph():
    data = _make_data([
        ("Line", 90, 1, 1, 1),
        ("one", 90, 1, 1, 1),
        ("Line", 88, 1, 1, 2),
        ("two", 88, 1, 1, 2),
    ])
    result = _reconstruct_paragraphs(data)
    assert result == "Line one\nLine two"


def test_reconstruct_skips_empty_tokens():
    data = _make_data([
        ("", -1, 1, 1, 1),
        ("Hello", 90, 1, 1, 1),
        ("  ", -1, 1, 1, 1),
        ("world", 88, 1, 1, 1),
    ])
    assert _reconstruct_paragraphs(data) == "Hello world"


# ---------------------------------------------------------------------------
# _run_ocr — integration of reconstruction + cleaning + empty-result guard
# ---------------------------------------------------------------------------


def _mock_data(words):
    """Return a minimal image_to_data dict for the given list of word strings."""
    return {
        "text": words + [""],
        "conf": [90] * len(words) + [-1],
        "block_num": [1] * len(words) + [0],
        "par_num": [1] * len(words) + [0],
        "line_num": [1] * len(words) + [0],
    }


def test_run_ocr_returns_text():
    image = MagicMock(spec=Image.Image)
    with patch("services.extractor.pytesseract.image_to_data", return_value=_mock_data(["Hello", "world"])):
        result = _run_ocr(image)
    assert result == "Hello world"


def test_run_ocr_raises_on_empty_result():
    image = MagicMock(spec=Image.Image)
    empty_data = {
        "text": [""],
        "conf": [-1],
        "block_num": [0],
        "par_num": [0],
        "line_num": [0],
    }
    with patch("services.extractor.pytesseract.image_to_data", return_value=empty_data):
        with pytest.raises(ValueError, match="no usable text"):
            _run_ocr(image)


def test_run_ocr_logs_confidence(caplog):
    import logging
    image = MagicMock(spec=Image.Image)
    with patch("services.extractor.pytesseract.image_to_data", return_value=_mock_data(["Hello", "world"])):
        with caplog.at_level(logging.DEBUG, logger="services.extractor"):
            _run_ocr(image)
    assert any("confidence" in r.message.lower() for r in caplog.records)
