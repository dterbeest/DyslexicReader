"""
Image preprocessing for OCR quality improvement.

Steps: convert to grayscale → binarize (Otsu threshold) → deskew.
"""
import io
import math

import cv2
import numpy as np
from PIL import Image


def preprocess_image(image: Image.Image) -> Image.Image:
    img_array = np.array(image.convert("RGB"))
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    deskewed = _deskew(binary)
    return Image.fromarray(deskewed)


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
