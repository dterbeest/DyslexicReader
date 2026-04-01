"""
PDF generation using fpdf2 with OpenDyslexic fonts.

OpenDyslexic Regular and Bold OTF files live in backend/fonts/.
"""
from __future__ import annotations

import re
from pathlib import Path

from fpdf import FPDF

from services.layout_ir import BlockKind, DocumentLayout, TextBlock

FONTS_DIR = Path(__file__).parent.parent / "fonts"

# (regular_file, bold_file, fpdf_font_name)
FONT_FILES = {
    "opendyslexic": ("OpenDyslexic-Regular.otf", "OpenDyslexic-Bold.otf", "OpenDyslexic"),
    "lexend":       ("Lexend-Regular.ttf",        "Lexend-Bold.ttf",        "Lexend"),
    "atkinson":     ("AtkinsonHyperlegible-Regular.ttf", "AtkinsonHyperlegible-Bold.ttf", "AtkinsonHyperlegible"),
}

FONT_SIZES = {"small": 12, "medium": 14, "large": 18}
LINE_SPACINGS = {"normal": 1.2, "relaxed": 1.5, "double": 2.0}
BG_COLORS = {
    "white": (255, 255, 255),
    "cream": (255, 253, 208),
    "yellow": (250, 255, 160),
    "blue": (208, 232, 255),
}

MARGIN_MM = 25
PT_TO_MM = 0.352778
# Heading size multipliers by level
_H1_MULTIPLIER = 1.6
_H2_MULTIPLIER = 1.3
# List item indent in mm per nesting level
_LIST_INDENT_MM = 10


def build_pdf(content: str | DocumentLayout, settings: dict) -> bytes:
    """Build a dyslexia-friendly PDF from either a plain string or a DocumentLayout."""
    if isinstance(content, str):
        layout = _str_to_layout(content)
    else:
        layout = content

    font_size_pt = FONT_SIZES.get(settings.get("font_size", "medium"), 14)
    line_spacing = LINE_SPACINGS.get(settings.get("line_spacing", "relaxed"), 1.5)
    bg_rgb = BG_COLORS.get(settings.get("bg_color", "white"), (255, 255, 255))

    font_key = settings.get("font_family", "opendyslexic")
    regular_file, bold_file, font_name = FONT_FILES.get(font_key, FONT_FILES["opendyslexic"])

    pdf = _DyslexicPDF(bg_rgb, font_name)
    pdf.set_margins(left=MARGIN_MM, top=MARGIN_MM, right=MARGIN_MM)
    pdf.set_auto_page_break(auto=True, margin=MARGIN_MM)

    pdf.add_font(font_name, style="", fname=str(FONTS_DIR / regular_file))
    pdf.add_font(font_name, style="B", fname=str(FONTS_DIR / bold_file))

    pdf.add_page()

    body_height_mm = font_size_pt * PT_TO_MM * line_spacing
    h1_size_pt = int(font_size_pt * _H1_MULTIPLIER)
    h2_size_pt = int(font_size_pt * _H2_MULTIPLIER)

    for block in layout.blocks:
        if block.kind == BlockKind.WHITESPACE:
            pdf.ln(body_height_mm * 1.5)
            continue

        text = block.text.strip()
        if not text:
            continue

        if block.kind == BlockKind.HEADING:
            if block.extra_space_before:
                pdf.ln(body_height_mm)
            size_pt = h1_size_pt if block.heading_level == 1 else h2_size_pt
            height_mm = size_pt * PT_TO_MM * line_spacing
            pdf.set_font(font_name, style="B", size=size_pt)
            pdf.multi_cell(0, height_mm, text)
            pdf.ln(height_mm * 0.5)

        elif block.kind == BlockKind.LIST_ITEM:
            indent = _LIST_INDENT_MM * max(1, block.indent_level)
            x = MARGIN_MM + indent
            available_w = pdf.w - x - MARGIN_MM
            pdf.set_x(x)
            pdf.set_font(font_name, size=font_size_pt)
            pdf.multi_cell(available_w, body_height_mm, text)
            pdf.ln(body_height_mm * 0.25)

        else:  # BODY
            if block.extra_space_before:
                pdf.ln(body_height_mm * 0.5)
            pdf.set_font(font_name, size=font_size_pt)
            pdf.multi_cell(0, body_height_mm, text)
            pdf.ln(body_height_mm * 0.5)

    return bytes(pdf.output())


def _str_to_layout(text: str) -> DocumentLayout:
    """Convert a plain string to a DocumentLayout using the legacy heading heuristic."""
    blocks: list[TextBlock] = []
    for paragraph in text.split("\n\n"):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        if _is_heading(paragraph):
            blocks.append(TextBlock(kind=BlockKind.HEADING, text=paragraph, heading_level=1))
        else:
            blocks.append(TextBlock(kind=BlockKind.BODY, text=paragraph))
    return DocumentLayout(blocks=blocks)


def _is_heading(paragraph: str) -> bool:
    """Detect single all-caps lines as headings."""
    lines = paragraph.strip().splitlines()
    if len(lines) != 1:
        return False
    line = lines[0].strip()
    letters = re.sub(r"[^a-zA-Z]", "", line)
    return bool(letters) and letters == letters.upper() and len(line) <= 80


class _DyslexicPDF(FPDF):
    """FPDF subclass that paints the background on every page and adds page numbers."""

    def __init__(self, bg_rgb: tuple[int, int, int], font_name: str):
        super().__init__()
        self._bg_rgb = bg_rgb
        self._font_name = font_name

    def header(self) -> None:
        r, g, b = self._bg_rgb
        self.set_fill_color(r, g, b)
        self.rect(0, 0, self.w, self.h, style="F")

    def footer(self) -> None:
        self.set_y(-15)
        self.set_font(self._font_name, size=9)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, str(self.page_no()), align="C")
        self.set_text_color(0, 0, 0)
