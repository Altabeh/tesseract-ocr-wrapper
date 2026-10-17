import ctypes

import pytest

import tesseract
from tesseract import PageSegMode, Tesseract, TesseractError

from conftest import render_text_image


def test_page_seg_mode_values():
    assert [int(mode) for mode in PageSegMode] == list(range(14))
    assert PageSegMode.AUTO == 3
    assert PageSegMode.SINGLE_LINE == 7


def test_to_char_p_p():
    vec = tesseract.to_char_p_p(["load_system_dawg", "F"])
    assert len(vec) == 2
    assert ctypes.string_at(vec[0]) == b"load_system_dawg"
    assert ctypes.string_at(vec[1]) == b"F"


def test_omp_thread_limit_is_set():
    assert tesseract.os.environ["OMP_THREAD_LIMIT"]


def test_missing_library_raises(monkeypatch):
    monkeypatch.setattr(Tesseract, "_lib", None)
    monkeypatch.setattr(tesseract.ctypes.util, "find_library", lambda name: None)
    with pytest.raises(TesseractError, match="library was not found"):
        Tesseract()


@pytest.mark.integration
def test_unknown_language_raises():
    with pytest.raises(TesseractError, match="Initialization failed"):
        Tesseract(language="no_such_language")


@pytest.mark.integration
@pytest.mark.parametrize("grayscale", [False, True])
def test_recognizes_image(grayscale):
    import cv2

    img = render_text_image("Hello Tesseract")
    if grayscale:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    height, width = img.shape[:2]
    depth = 1 if grayscale else 3

    tess = Tesseract()
    tess.set_psm(PageSegMode.SINGLE_LINE)
    tess.set_image(img.ctypes, width, height, depth)
    assert tess.get_text().strip() == "Hello Tesseract"


@pytest.mark.integration
def test_blank_image_returns_empty_string():
    import numpy as np

    img = np.full((100, 100), 255, np.uint8)
    tess = Tesseract()
    tess.set_image(img.ctypes, 100, 100, 1)
    assert tess.get_text().strip() == ""
