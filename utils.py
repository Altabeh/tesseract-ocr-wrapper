import concurrent.futures as future
import os
from pathlib import Path
from subprocess import PIPE, CalledProcessError, Popen, check_output
from tempfile import TemporaryDirectory

import cv2
from pdf2image import convert_from_path

from tesseract import Tesseract, PageSegMode

__all__ = [
    "pdf_to_text",
    "ocr_to_text",
    "get_page_count",
]

TESS = Tesseract()

def pdf_to_text(pdf_path:str , target_dir: str):
    """
    Convert pdf at `pdf_path` to a txt file in `target_dir` using XpdfReader's pdftotext.
    """
    file_name = Path(pdf_path).stem
    command = [
        "pdftotext",
        "-layout",
        pdf_path,
        str(Path(target_dir) / f"{file_name}.txt"),
    ]
    proc = Popen(command, stdout=PIPE, stderr=PIPE)
    proc.wait()
    (stdout, stderr) = proc.communicate()
    if proc.returncode:
        return stderr
    return ""


def _get_tesseract_text(img_path: str, **kwargs):
    """
    Use Tesseract API to get the text from the images directly.

    Keywords
    --------
    A dictionary of key, val that Tesseract API can accept.
    """
    grayscale = kwargs.get("grayscale", False)
    psm = int(kwargs.get("psm", PageSegMode.AUTO))
    imcv = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE if grayscale else cv2.IMREAD_COLOR)
    for key, val in kwargs.items():
        TESS.set_variable(key, str(val))
    TESS.set_psm(psm)
    height, width, *rest = imcv.shape
    depth = (rest or [1])[0]
    TESS.set_image(imcv.ctypes, width, height, depth)
    gettext = TESS.get_text()
    return gettext


def _wrap_get_tesseract_text(img_path: str, kwargs):
    """
    A wrapper for `get_tesseract_text` to be used in multiprocessing/concurrency.
    """
    return _get_tesseract_text(img_path, **kwargs)


def ocr_to_text(pdf_path: str, batch_size: int=10, first_page: int=1, last_page: int=0, **kwargs):
    """
    Convert ocr to text using path2image, cv2 and tesseract api.
    `kwargs` belong to the function `get_tesseract_text`.

    Args
    ----
    :param pdf_path: ---> str: the path to a pdf document.
    :param batch_size: ---> int: size of batches of converted pages
                                 fed into `get_tesseract_text`.
    """
    resolution = kwargs.get("user_defined_dpi", 250)
    grayscale = kwargs.get("grayscale", False)
    if last_page <= 0:
        last_page = get_page_count(pdf_path) + last_page
    cpus = os.cpu_count()
    # To use up all cpus
    if cpus > batch_size:
        batch_size = cpus
    iter_ = 0
    for page in range(first_page, last_page + 1, batch_size):
        with TemporaryDirectory() as path:
            path_to_pages = convert_from_path(
                pdf_path,
                output_folder=path,
                fmt="tiff",
                dpi=int(resolution),
                first_page=page,
                last_page=min(page + batch_size - 1, last_page),
                paths_only=True,
                grayscale=bool(grayscale),
            )

            with future.ProcessPoolExecutor(max_workers=cpus) as executor:
                tasks = {
                    executor.submit(_wrap_get_tesseract_text, page, kwargs): i
                    + 1
                    + iter_ * batch_size
                    for i, page in enumerate(path_to_pages)
                }
                for f in future.as_completed(tasks):
                    page_number = tasks[f]
                    try:
                        data = f.result(), page_number
                        yield data
                    except Exception as e:
                        print(f"page #{page_number} generated an exception: {e}")
        iter_ += 1


def get_page_count(pdf_path: str):
    """
    Use XpdfReader's pdfinfo to extract the number of pages in a pdf file.
    """
    try:
        output = check_output(["pdfinfo", pdf_path]).decode()
        pages_line = [line for line in output.splitlines() if "Pages:" in line][0]
        num_pages = int(pages_line.split(":")[1])
        return num_pages
    except (CalledProcessError, UnicodeDecodeError):
        return 0
