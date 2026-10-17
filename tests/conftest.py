import ctypes.util
import shutil
import sys
from pathlib import Path

import pytest

REPO_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_DIR))

HAS_TESSERACT = ctypes.util.find_library("tesseract") is not None
HAS_POPPLER = shutil.which("pdfinfo") is not None and shutil.which("pdftoppm") is not None

PAGE_TEXTS = ["Hello from page one", "Second page of text"]


def pytest_collection_modifyitems(config, items):
    if HAS_TESSERACT and HAS_POPPLER:
        return
    skip = pytest.mark.skip(reason="requires libtesseract and poppler-utils")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip)


def render_text_image(text: str):
    import numpy as np
    import cv2

    img = np.full((400, 1400, 3), 255, np.uint8)
    cv2.putText(img, text, (40, 220), cv2.FONT_HERSHEY_SIMPLEX, 2.5, (0, 0, 0), 5)
    return img


@pytest.fixture(scope="session")
def sample_pdf(tmp_path_factory):
    """A scanned-style (image only) PDF with one line of text per page."""
    from PIL import Image

    pages = [Image.fromarray(render_text_image(text)) for text in PAGE_TEXTS]
    path = tmp_path_factory.mktemp("pdf") / "sample.pdf"
    pages[0].save(path, save_all=True, append_images=pages[1:], resolution=100)
    return path
