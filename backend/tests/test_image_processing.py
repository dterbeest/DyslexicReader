import numpy as np
import pytest
from PIL import Image

from utils.image_processing import (
    preprocess_image,
    _upscale_if_small,
    _denoise,
    _apply_clahe,
    _deskew,
)


def _gray(h: int, w: int, fill: int = 128) -> np.ndarray:
    return np.full((h, w), fill, dtype=np.uint8)


def _random_gray(h: int, w: int) -> np.ndarray:
    rng = np.random.default_rng(42)
    return rng.integers(0, 256, size=(h, w), dtype=np.uint8)


# --- _upscale_if_small ---

def test_upscale_small_image():
    img = _gray(200, 300)
    result = _upscale_if_small(img)
    assert min(result.shape) >= 1000


def test_no_upscale_large_image():
    img = _gray(1200, 1600)
    result = _upscale_if_small(img)
    assert result.shape == (1200, 1600)


def test_upscale_preserves_aspect_ratio():
    img = _gray(400, 600)  # 2:3 ratio, short side=400
    result = _upscale_if_small(img)
    h, w = result.shape
    assert abs(w / h - 600 / 400) < 0.01


# --- _denoise ---

def test_denoise_returns_same_shape():
    img = _random_gray(200, 300)
    result = _denoise(img)
    assert result.shape == img.shape
    assert result.dtype == np.uint8


# --- _apply_clahe ---

def test_clahe_output_shape():
    img = _random_gray(200, 300)
    result = _apply_clahe(img)
    assert result.shape == img.shape
    assert result.dtype == np.uint8


# --- _deskew ---

def test_deskew_straight_image_unchanged_shape():
    # Horizontal line — already straight, deskew should return same shape
    img = np.full((200, 400), 255, dtype=np.uint8)
    img[100, 50:350] = 0  # horizontal line
    result = _deskew(img)
    assert result.shape == img.shape


def test_deskew_too_few_dark_pixels_returns_input():
    img = np.full((100, 100), 255, dtype=np.uint8)
    result = _deskew(img)
    assert result is img  # unchanged reference when no dark pixels


# --- full pipeline ---

def test_full_pipeline_completes():
    rng = np.random.default_rng(0)
    arr = rng.integers(0, 256, size=(700, 500, 3), dtype=np.uint8)
    pil_img = Image.fromarray(arr, mode="RGB")
    result = preprocess_image(pil_img)
    assert isinstance(result, Image.Image)


def test_grayscale_output():
    rng = np.random.default_rng(1)
    arr = rng.integers(0, 256, size=(300, 400, 3), dtype=np.uint8)
    pil_img = Image.fromarray(arr, mode="RGB")
    result = preprocess_image(pil_img)
    assert result.mode == "L"
