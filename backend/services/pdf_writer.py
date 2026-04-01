"""
PDF generation using fpdf2 with OpenDyslexic fonts.

OpenDyslexic Regular and Bold OTF files live in backend/fonts/.
"""
import re
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

MARGIN_MM = 25
PT_TO_MM = 0.352778
HEADING_SIZE_MULTIPLIER = 1.4


def build_pdf(text: str, settings: dict) -> bytes:
    font_size_pt = FONT_SIZES.get(settings.get("font_size", "medium"), 14)
    line_spacing = LINE_SPACINGS.get(settings.get("line_spacing", "relaxed"), 1.5)
    bg_rgb = BG_COLORS.get(settings.get("bg_color", "white"), (255, 255, 255))

    pdf = _DyslexicPDF(bg_rgb)
    pdf.set_margins(left=MARGIN_MM, top=MARGIN_MM, right=MARGIN_MM)
    pdf.set_auto_page_break(auto=True, margin=MARGIN_MM)

    pdf.add_font("OpenDyslexic", style="", fname=str(FONTS_DIR / "OpenDyslexic-Regular.otf"))
    pdf.add_font("OpenDyslexic", style="B", fname=str(FONTS_DIR / "OpenDyslexic-Bold.otf"))

    pdf.add_page()

    body_height_mm = font_size_pt * PT_TO_MM * line_spacing
    heading_size_pt = int(font_size_pt * HEADING_SIZE_MULTIPLIER)
    heading_height_mm = heading_size_pt * PT_TO_MM * line_spacing

    for paragraph in text.split("\n\n"):
        paragraph = paragraph.strip()
        if not paragraph:
            continue

        if _is_heading(paragraph):
            pdf.set_font("OpenDyslexic", style="B", size=heading_size_pt)
            pdf.multi_cell(0, heading_height_mm, paragraph)
            pdf.ln(heading_height_mm * 0.5)
        else:
            pdf.set_font("OpenDyslexic", size=font_size_pt)
            pdf.multi_cell(0, body_height_mm, paragraph)
            pdf.ln(body_height_mm * 0.5)

    return bytes(pdf.output())


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

    def __init__(self, bg_rgb: tuple[int, int, int]):
        super().__init__()
        self._bg_rgb = bg_rgb

    def header(self) -> None:
        r, g, b = self._bg_rgb
        self.set_fill_color(r, g, b)
        self.rect(0, 0, self.w, self.h, style="F")

    def footer(self) -> None:
        self.set_y(-15)
        self.set_font("OpenDyslexic", size=9)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, str(self.page_no()), align="C")
        self.set_text_color(0, 0, 0)
