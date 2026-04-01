# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

DyslexicReader — a free, anonymous web app that converts images and PDFs into dyslexia-friendly PDFs using the OpenDyslexic font. See `plan.md` for full architecture decisions and rationale.

## Repository Structure

This is a monorepo with two top-level packages:

```
frontend/   — React + Vite (TypeScript)
backend/    — Python + FastAPI
```

Neither package exists yet. When scaffolding, follow this structure.

## Frontend (`frontend/`)

**Stack:** React, Vite, TypeScript, Tailwind CSS

```bash
cd frontend
npm install
npm run dev          # dev server
npm run build        # production build → dist/
npm run lint         # eslint
npm run test         # vitest
npm run test -- -t "test name"  # single test
```

Environment variable: `VITE_API_URL` — points to the backend (set in `.env.local` for dev, Netlify dashboard for prod).

Deployed to **Netlify** via `netlify.toml`. Auto-deploys on push to `main`.

## Backend (`backend/`)

**Stack:** Python 3.11+, FastAPI, uvicorn

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload       # dev server (port 8000)
uvicorn main:app --host 0.0.0.0 # production (used in Dockerfile)
pytest                          # all tests
pytest tests/test_ocr.py        # single file
pytest -k "test_name"           # single test
```

Deployed to **Railway** via `Dockerfile`. Auto-deploys on push to `main`.

**System dependencies required** (installed in Dockerfile, needed locally too):
- `tesseract-ocr` + `tesseract-ocr-eng` (OCR engine)
- `poppler-utils` (PDF rasterization via pdf2image)

## Key Backend Dependencies

| Package | Purpose |
|---|---|
| `pytesseract` | Tesseract OCR wrapper |
| `Pillow` + `opencv-python-headless` | Image preprocessing (deskew, contrast, binarization) |
| `pdfplumber` | Extract embedded text from digital PDFs |
| `pdf2image` | Rasterize scanned PDF pages for OCR |
| `fpdf2` | Generate output PDFs with custom TTF fonts |
| `python-magic` | Validate uploads by magic bytes, not extension |
| `slowapi` | IP-based rate limiting for FastAPI |

## Architecture

### Conversion Pipeline

`POST /convert` (multipart: file + settings) →

1. **Validate** — magic bytes check (not extension), size limits (10MB images / 25MB PDFs), 50-page cap for PDFs
2. **Extract text** — branch on file type:
   - Image (JPG/PNG): preprocess → pytesseract OCR
   - Digital PDF (embedded text): pdfplumber extraction
   - Scanned PDF (image-only pages): pdf2image rasterize → preprocess → pytesseract OCR
   - Mixed PDF: handle per-page
3. **Generate PDF** — fpdf2 with OpenDyslexic TTF, applying user settings
4. **Return** — PDF as streaming response (`application/pdf`)

Nothing is written to disk. All file data lives in memory (`io.BytesIO`) and is discarded after the response. No logging of file contents.

### User Settings (passed as form fields)

| Field | Values |
|---|---|
| `font_size` | `small` (12pt) / `medium` (14pt) / `large` (18pt) |
| `line_spacing` | `normal` (1.2×) / `relaxed` (1.5×) / `double` (2.0×) |
| `bg_color` | `white` / `cream` (#FFFDD0) / `yellow` (#FAFFA0) / `blue` (#D0E8FF) |

### API Endpoints

- `GET /health` — health check, not rate limited
- `POST /convert` — rate limited: 10 requests/IP/hour; returns PDF or JSON error

### Fonts

OpenDyslexic Regular and Bold `.ttf` files live in `backend/fonts/`. These must be registered with fpdf2 at startup. Do not substitute other fonts.

## Critical Constraints

- **Zero persistence** — no file writes, no database, no logging of user content. This is a privacy commitment stated in the UI.
- **English only** — Tesseract is configured for English (`lang='eng'`) in MVP. Architecture should make adding languages easy later.
- **Reflowed output only** — original document layout is intentionally discarded. Output is clean paragraphs in OpenDyslexic. Do not attempt layout preservation.
- **Anonymous** — no auth, no sessions, no user tracking.
