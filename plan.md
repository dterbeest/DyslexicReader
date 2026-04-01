# DyslexicReader — MVP Plan

## Overview

DyslexicReader is a free, anonymous web app that converts any image or PDF into a
clean, reformatted PDF using dyslexia-friendly typography. Users upload a file,
choose display preferences, and download a reader-optimized PDF — no account
required, no data stored.

---

## Problem

Standard PDFs and scanned documents use fonts, spacing, and layouts that create
significant friction for dyslexic readers. There is no simple, free tool that
handles the full pipeline: OCR → reformat → export in a dyslexia-friendly font.

---

## Architecture

```
[User Browser]
     |
     | upload (JPG/PNG/PDF) + settings
     v
[React/Vite Frontend]  ──── static deploy on Netlify
     |
     | multipart POST /convert
     v
[Python/FastAPI Backend]  ── containerized deploy on Railway
     |
     ├── PDF native text extraction (pdfplumber)
     ├── Image preprocessing (Pillow / OpenCV)  ← for photos/scanned pages
     ├── OCR (pytesseract / Tesseract)
     ├── Text cleaning & paragraph reconstruction
     └── PDF generation (fpdf2 + OpenDyslexic TTF)
     |
     | returns PDF binary (in-memory, never written to disk)
     v
[User Browser] — downloads result.pdf
```

**Zero persistence:** files are processed entirely in memory. Nothing is written to
disk or stored. Uploaded content is discarded immediately after the response.

---

## Tech Stack

| Layer | Technology | Reason |
|---|---|---|
| Frontend | React + Vite | Fast dev, excellent file upload UX |
| Backend | Python + FastAPI | Best OCR/PDF ecosystem, async, auto docs |
| OCR | pytesseract (Tesseract) | Free, runs locally, no API costs |
| Image preprocessing | Pillow + OpenCV | Deskew, contrast normalization |
| Native PDF text | pdfplumber | Reliable text + layout extraction |
| PDF generation | fpdf2 | Lightweight, supports custom TTF fonts |
| Font | OpenDyslexic (Regular + Bold) | Open source, widely validated |
| Frontend hosting | Netlify | Free tier, instant static deploys |
| Backend hosting | Railway | No sleep on free tier, easy Docker deploys |

---

## User Flow (MVP)

1. User lands on homepage — brief explainer + upload area
2. User drags/drops or selects a file (JPG, PNG, or PDF — max 10MB image / 25MB PDF)
3. User selects output preferences:
   - **Font size**: Small / Medium / Large
   - **Line spacing**: Normal / Relaxed / Double
   - **Page background**: White / Cream / Light Yellow / Light Blue
4. User clicks "Convert"
5. Progress indicator shown while processing
6. Download button appears — user gets `result.pdf`

---

## Customization Options (MVP)

| Option | Choices |
|---|---|
| Font | OpenDyslexic Regular (body), OpenDyslexic Bold (headings) |
| Font size | Small (12pt) / Medium (14pt) / Large (18pt) |
| Line spacing | Normal (1.2×) / Relaxed (1.5×) / Double (2.0×) |
| Background color | White / Cream (#FFFDD0) / Yellow (#FAFFA0) / Blue (#D0E8FF) |

---

## Input Handling

| Input | Processing |
|---|---|
| Digital PDF (embedded text) | Extract text directly with pdfplumber, skip OCR |
| Scanned PDF (image-based pages) | Rasterize pages → preprocess → pytesseract OCR |
| JPG / PNG photo | Preprocess (deskew, contrast) → pytesseract OCR |

**Limits:** 10MB max for images, 25MB max for PDFs, 50 pages max per PDF.

---

## Constraints & Non-Goals (MVP)

- **English only** — Tesseract language packs for other languages are v2
- **Reflowed text output only** — original layout/columns/images not preserved
- **No user accounts** — anonymous, stateless
- **No file history** — each session is independent
- **No mobile-specific UI** — responsive but not mobile-first
- **No DOCX/TIFF support** — v2

---

## Phased Roadmap

### MVP (v1.0)
- File upload UI with drag-and-drop
- Image preprocessing pipeline
- OCR via pytesseract
- Native PDF text extraction
- fpdf2 output with OpenDyslexic
- Font size / line spacing / background color controls
- In-memory processing (zero persistence)
- Rate limiting (IP-based, 10 requests/hour)
- Error handling + user feedback
- Deploy: Netlify (frontend) + Railway (backend)

### v2
- Multi-language OCR support
- Layout-aware output (preserve headings, detect columns)
- DOCX and TIFF input support
- Word-level highlighting / reading mode in browser
- Accessibility audit

### v3
- User accounts + conversion history
- Batch upload
- Browser extension
- API access

---

## Privacy Commitment

DyslexicReader processes all files in memory and retains nothing. No file content,
metadata, or personal data is stored, logged, or transmitted to third parties.
This commitment is stated clearly in the UI.
