"""
PDF generation using fpdf2 with OpenDyslexic TTF fonts.

Fonts must be present at backend/fonts/OpenDyslexic-Regular.ttf
and backend/fonts/OpenDyslexic-Bold.ttf.
"""
import os
from pathlib import Path

from fpdf import FPDF

FONTS_DIR = Path(__file__).parent.parent / "fonts"

FONT_SIZES = {"small": 12, "medium": 14, "large": 18}
LINE_SPACINGS = {"normal": 1.2, "relaxed": 1.5, "double": 2.0}
BG_COLORS = {
    "white": (255, 255, 255),
    "cream": (255, 253, 208),
    "yellow": (250, 255, 160),
    "blue": (208, 232, 255),
}

# Points-to-mm conversion (fpdf2 uses mm)
PT_TO_MM = 0.352778


def build_pdf(text: str, settings: dict) -> bytes:
    font_size_pt = FONT_SIZES.get(settings.get("font_size", "medium"), 14)
    line_spacing = LINE_SPACINGS.get(settings.get("line_spacing", "relaxed"), 1.5)
    bg_rgb = BG_COLORS.get(settings.get("bg_color", "white"), (255, 255, 255))

    pdf = FPDF()
    pdf.set_margins(left=20, top=20, right=20)
    pdf.set_auto_page_break(auto=True, margin=20)

    pdf.add_font("OpenDyslexic", style="", fname=str(FONTS_DIR / "OpenDyslexic-Regular.ttf"))
    pdf.add_font("OpenDyslexic", style="B", fname=str(FONTS_DIR / "OpenDyslexic-Bold.ttf"))

    pdf.add_page()
    _set_bg(pdf, bg_rgb)

    pdf.set_font("OpenDyslexic", size=font_size_pt)

    line_height_mm = font_size_pt * PT_TO_MM * line_spacing

    for paragraph in text.split("\n\n"):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        pdf.multi_cell(0, line_height_mm, paragraph)
        pdf.ln(line_height_mm * 0.5)

    return bytes(pdf.output())


def _set_bg(pdf: FPDF, rgb: tuple[int, int, int]) -> None:
    r, g, b = rgb
    pdf.set_fill_color(r, g, b)
    pdf.rect(0, 0, pdf.w, pdf.h, style="F")
