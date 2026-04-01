"""
Image preprocessing for OCR quality improvement.

Pipeline: grayscale → downscale if large → upscale if small → sharpen → denoise → CLAHE → adaptive threshold → deskew.
"""
import cv2
import numpy as np
from PIL import Image

# Minimum size (shortest side in pixels) before upscaling — ~150 DPI minimum for decent OCR
_MIN_SIDE = 1000
# Maximum size (longest side in pixels) before downscaling — phone photos are often 12MP+
_MAX_SIDE = 2400


def preprocess_image(image: Image.Image) -> Image.Image:
    img_array = np.array(image.convert("RGB"))
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    gray = _downscale_if_large(gray)
    gray = _upscale_if_small(gray)
    gray = _sharpen(gray)
    gray = _denoise(gray)
    gray = _apply_clahe(gray)
    binary = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 15
    )
    deskewed = _deskew(binary)
    return Image.fromarray(deskewed)


def _downscale_if_large(gray: np.ndarray) -> np.ndarray:
    h, w = gray.shape
    longest = max(h, w)
    if longest <= _MAX_SIDE:
        return gray
    scale = _MAX_SIDE / longest
    new_w, new_h = int(w * scale), int(h * scale)
    return cv2.resize(gray, (new_w, new_h), interpolation=cv2.INTER_AREA)


def _upscale_if_small(gray: np.ndarray) -> np.ndarray:
    h, w = gray.shape
    shortest = min(h, w)
    if shortest >= _MIN_SIDE:
        return gray
    scale = _MIN_SIDE / shortest
    new_w, new_h = int(w * scale), int(h * scale)
    return cv2.resize(gray, (new_w, new_h), interpolation=cv2.INTER_CUBIC)


def _sharpen(gray: np.ndarray) -> np.ndarray:
    """Sharpen edges after upscaling — INTER_CUBIC blurs slightly, hurting OCR accuracy."""
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    return cv2.filter2D(gray, -1, kernel)


def _denoise(gray: np.ndarray) -> np.ndarray:
    return cv2.medianBlur(gray, 3)


def _apply_clahe(gray: np.ndarray) -> np.ndarray:
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(gray)


def _deskew(binary: np.ndarray) -> np.ndarray:
    coords = np.column_stack(np.where(binary < 128))
    if len(coords) < 5:
        return binary
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = 90 + angle
    if abs(angle) < 0.5:
        return binary
    h, w = binary.shape
    center = (w // 2, h // 2)
    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(binary, matrix, (w, h), flags=cv2.INTER_CUBIC, borderValue=255)
    return rotated
