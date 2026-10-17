# tesseract-ocr-wrapper

A lightweight Python wrapper around the [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) C API, built for extracting text from large numbers of scanned PDFs quickly and with low memory usage.

```python
from utils import ocr_to_text

pages = sorted(ocr_to_text("scan.pdf", grayscale=True), key=lambda page: page[1])
text = "\n".join(page_text for page_text, _ in pages)
```

Or, without installing anything except Docker:

```bash
docker build -t tesseract-ocr-wrapper .
docker run --rm -v "$PWD:/data" tesseract-ocr-wrapper scan.pdf
```

## Contents

- [Why not pytesseract?](#why-not-pytesseract)
- [Docker](#docker)
- [Installation](#installation)
  - [Debian / Ubuntu](#debian--ubuntu)
  - [RHEL / Rocky / AlmaLinux / Fedora](#rhel--rocky--almalinux--fedora)
  - [macOS](#macos)
  - [Other systems](#other-systems)
  - [Installer options](#installer-options)
- [Usage](#usage)
  - [Command line](#command-line)
  - [OCR a PDF](#ocr-a-pdf)
  - [Extract embedded text without OCR](#extract-embedded-text-without-ocr)
  - [Use the Tesseract API directly](#use-the-tesseract-api-directly)
- [API reference](#api-reference)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## Why not pytesseract?

[pytesseract](https://pypi.org/project/pytesseract/) shells out to the `tesseract` binary for every image. This wrapper calls `libtesseract` in-process through `ctypes`, and adds two features aimed at batch processing:

- **Parallel by default.** `ocr_to_text` sends every page to a `ProcessPoolExecutor` and yields `(text, page_number)` tuples as soon as each page finishes. You don't wait for the whole document. Results can arrive out of order, so sort by page number if order matters.
- **Bounded memory.** Pages are rendered to images in a `TemporaryDirectory` one batch at a time, and each batch is deleted once it has been processed. Memory stays flat whether you OCR one PDF or thousands.

Tesseract's own OpenMP threading is turned off (`OMP_THREAD_LIMIT=1`) because it competes with the process pool and slows things down. To override this, set the variable yourself before importing the wrapper.

## Docker

There are two images. Both run [`ocr.py`](#command-line) as their entrypoint, with `/data` as the working directory, so mount the folder that holds your PDFs there.

| File | Base image | How Tesseract is installed | Size |
| --- | --- | --- | --- |
| `Dockerfile` | `python:3.13-slim` (Debian) | Distribution packages via `apt-get` | ~630 MB |
| `Dockerfile.rhel` | Red Hat UBI 9 (RHEL 9) | Leptonica 1.87.0 and Tesseract 5.5.3 compiled from source in a build stage | ~890 MB |

```bash
# Debian
docker build -t tesseract-ocr-wrapper .
docker run --rm -v "$PWD:/data" tesseract-ocr-wrapper scan.pdf > scan.txt

# RHEL 9
docker build -f Dockerfile.rhel -t tesseract-ocr-wrapper:rhel .
docker run --rm -v "$PWD:/data" tesseract-ocr-wrapper:rhel --grayscale -o out/ *.pdf
```

The RHEL image uses Red Hat's [Universal Base Image](https://catalog.redhat.com/software/base-images), which is a real RHEL userland that's free to use and redistribute, with no subscription needed. It builds in two stages, so the compiler toolchain isn't part of the final image. To build on a different RHEL-compatible base, pass it as a build argument (the image needs `python3.12` and the packages listed in `Dockerfile.rhel`):

```bash
docker build -f Dockerfile.rhel --build-arg UBI_IMAGE=rockylinux/rockylinux:9 -t tesseract-ocr-wrapper:rocky .
```

To use the library from Python inside a container instead of the CLI, override the entrypoint:

```bash
docker run --rm -it -v "$PWD:/data" --entrypoint python tesseract-ocr-wrapper
>>> import sys; sys.path.insert(0, "/app")
>>> from utils import ocr_to_text
```

## Installation

You need:

| Dependency | Purpose |
| --- | --- |
| Tesseract (`libtesseract`) + English language data | The OCR engine |
| Poppler (`pdfinfo`, `pdftoppm`, `pdftotext`) | Counting PDF pages and rendering them to images |
| Python 3.9+ with `pdf2image` and `opencv-python-headless` | Python-side glue |

The included installer script, `_sys.py`, detects your platform and installs everything. Run it inside a virtual environment:

```bash
git clone https://github.com/Altabeh/tesseract-ocr-wrapper.git
cd tesseract-ocr-wrapper
python3 -m venv .venv
source .venv/bin/activate
python _sys.py
```

When it finishes, it checks that `pdfinfo` is on your `PATH` and that the dynamic loader can find `libtesseract`.

### Debian / Ubuntu

On Debian, Ubuntu, and their derivatives (Mint, Pop!_OS, Raspberry Pi OS, ...), the installer uses `apt-get` to install the distribution packages:

```bash
sudo apt-get install python3-venv   # if venv isn't available yet
python _sys.py
```

This is equivalent to:

```bash
sudo apt-get update
sudo apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-eng poppler-utils
pip install -r requirements.txt
```

Tested on Debian 12 (bookworm), Debian 13 (trixie), and Ubuntu 24.04. For other languages, install the matching package, for example `sudo apt-get install tesseract-ocr-deu` for German.

### RHEL / Rocky / AlmaLinux / Fedora

On RHEL-family systems, the installer uses `dnf` (or `yum`) to install Poppler and the build tools. It then compiles **Leptonica 1.87.0** and **Tesseract 5.5.3** from source into `/usr/local`, registers `/usr/local/lib` with the dynamic linker, and downloads the fast English model into `/usr/local/share/tessdata`. Expect this to take a few minutes.

```bash
sudo dnf install python3.12    # any Python 3.9+ works
python3.12 -m venv .venv && source .venv/bin/activate
python _sys.py
```

Tested on RHEL 9 (UBI 9). Every package it needs is in the standard BaseOS and AppStream repositories, so EPEL isn't required. To add another language, download `<lang>.traineddata` from [tessdata_fast](https://github.com/tesseract-ocr/tessdata_fast) into `/usr/local/share/tessdata`.

### macOS

The installer uses [Homebrew](https://brew.sh):

```bash
python _sys.py   # runs: brew install tesseract poppler
```

### Other systems

Install Tesseract (with its shared library) and Poppler using your system's package manager. Then install only the Python requirements:

```bash
python _sys.py --skip-system
# or simply: pip install -r requirements.txt
```

### Installer options

| Flag | Effect |
| --- | --- |
| `--dry-run` | Print every command without running anything |
| `--skip-system` | Don't install system packages; only run `pip install` |
| `--skip-pip` | Only install system packages |

Run `python _sys.py --dry-run` first to see exactly what will happen on your machine. If you're not root, the installer uses `sudo` for commands that need it.

## Usage

Run these examples from the repository root, or add it to your `PYTHONPATH`.

### Command line

`ocr.py` OCRs one or more PDFs. By default it prints the text to stdout; with `-o DIR`, it writes `DIR/<name>.txt` for each input instead.

```bash
python ocr.py scan.pdf > scan.txt
python ocr.py --grayscale --dpi 300 -o out/ invoices/*.pdf
python ocr.py --first-page 2 --last-page 5 --psm 6 -c preserve_interword_spaces=1 scan.pdf
```

| Option | Description |
| --- | --- |
| `-o`, `--output-dir DIR` | Write one `.txt` per PDF into `DIR` |
| `--first-page N`, `--last-page N` | Page range. `--last-page` of `0` or less counts back from the end |
| `--dpi N` | Render resolution (default `250`) |
| `--psm N` | [Page segmentation mode](#tesseractpagesegmode) (default `3`) |
| `--grayscale` | Render pages in grayscale |
| `-c KEY=VALUE` | Set a Tesseract variable; can be repeated |

### OCR a PDF

```python
from utils import ocr_to_text

OCR_CONFIG = {
    "grayscale": True,         # render pages in grayscale (faster, usually just as accurate)
    "user_defined_dpi": 250,   # render resolution; also passed to Tesseract
}

pages = sorted(ocr_to_text("scan.pdf", **OCR_CONFIG), key=lambda page: page[1])
text = "\n".join(page_text for page_text, _ in pages)
```

To OCR only some pages, pass `first_page` and/or `last_page`. A non-positive `last_page` counts back from the end:

```python
ocr_to_text("scan.pdf", first_page=3, last_page=10)  # pages 3-10
ocr_to_text("scan.pdf", last_page=-1)                # every page but the last
```

To change the page segmentation mode, use `psm`:

```python
from tesseract import PageSegMode

ocr_to_text("receipt.pdf", psm=PageSegMode.SPARSE_TEXT)
```

### Extract embedded text without OCR

If a PDF already contains a text layer (it wasn't scanned), `pdf_to_text` is much faster. It runs `pdftotext -layout` and writes `<name>.txt` to the target directory:

```python
from utils import pdf_to_text

error = pdf_to_text("report.pdf", "output/")
if error:
    print(error.decode())
```

### Use the Tesseract API directly

`Tesseract` works on any image buffer, such as a NumPy array from OpenCV:

```python
import cv2
from tesseract import Tesseract, PageSegMode

tess = Tesseract(language="eng")
tess.set_psm(PageSegMode.SINGLE_LINE)

img = cv2.imread("line.png", cv2.IMREAD_GRAYSCALE)
height, width = img.shape
tess.set_image(img.ctypes, width, height, bytes_per_pixel=1)
print(tess.get_text())
```

## API reference

### `utils.ocr_to_text(pdf_path, batch_size=10, first_page=1, last_page=0, **kwargs)`

A generator that yields `(text, page_number)` tuples, in completion order.

| Argument | Description |
| --- | --- |
| `pdf_path` | Path to the PDF |
| `batch_size` | Pages rendered per batch. Raised to `os.cpu_count()` if lower |
| `first_page`, `last_page` | Page range (1-indexed, inclusive). `last_page <= 0` is relative to the last page |
| `grayscale` | Render and read pages in grayscale |
| `user_defined_dpi` | Render DPI (default `250`) |
| `psm` | A `PageSegMode` value (default `PageSegMode.AUTO`) |
| any other key | Passed to Tesseract as a variable via `set_variable(key, value)` |

### `utils.pdf_to_text(pdf_path, target_dir)`

Writes the PDF's embedded text to `target_dir/<name>.txt`. Returns `""` on success, or `pdftotext`'s stderr as bytes on failure.

### `utils.get_page_count(pdf_path)`

Returns the number of pages reported by `pdfinfo`, or `0` if it can't be read.

### `tesseract.Tesseract(language="eng", datapath=None, lib_path=None)`

| Method | Description |
| --- | --- |
| `set_image(imagedata, width, height, bytes_per_pixel, bytes_per_line=0)` | Set the image to recognize. `bytes_per_pixel` is `1` for grayscale and `3` for RGB/BGR |
| `set_psm(mode)` | Set the page segmentation mode |
| `set_variable(key, value)` | Set a Tesseract parameter, like `-c key=value` on the command line |
| `get_text()` | Run recognition and return the text as `str` |
| `get_utf8_text()` | Same as `get_text()`, but returns raw UTF-8 `bytes` |

`datapath` points to a custom `tessdata` directory. `lib_path` points to a specific `libtesseract` file if the library can't be found automatically.

### `tesseract.PageSegMode`

| Value | Name | Meaning |
| --- | --- | --- |
| 0 | `OSD_ONLY` | Orientation and script detection only |
| 1 | `AUTO_OSD` | Automatic segmentation with OSD |
| 2 | `AUTO_ONLY` | Automatic segmentation, no OSD or OCR |
| 3 | `AUTO` | Fully automatic segmentation, no OSD (default for `ocr_to_text`) |
| 4 | `SINGLE_COLUMN` | A single column of text of variable sizes |
| 5 | `SINGLE_BLOCK_VERT_TEXT` | A single uniform block of vertical text |
| 6 | `SINGLE_BLOCK` | A single uniform block of text |
| 7 | `SINGLE_LINE` | A single text line |
| 8 | `SINGLE_WORD` | A single word |
| 9 | `CIRCLE_WORD` | A single word in a circle |
| 10 | `SINGLE_CHAR` | A single character |
| 11 | `SPARSE_TEXT` | As much text as possible, in no particular order |
| 12 | `SPARSE_TEXT_OSD` | Sparse text with OSD |
| 13 | `RAW_LINE` | A single text line, bypassing Tesseract-specific hacks |

## Troubleshooting

**`TesseractError: tesseract library was not found`**: `libtesseract` isn't installed or the loader can't see it. On Debian/Ubuntu, run `sudo apt-get install tesseract-ocr`. If you built from source, run `sudo ldconfig`, or pass `lib_path="/path/to/libtesseract.so"` to `Tesseract(...)`.

**`TesseractError: Initialization failed`**: the language data is missing. Install the language pack (e.g. `tesseract-ocr-eng`), or point `datapath` at a directory containing `<lang>.traineddata`.

**`error: externally-managed-environment` from pip**: newer Debian and Ubuntu releases block `pip install` into the system Python. Create and activate a virtual environment first (see [Installation](#installation)).

**`PDFInfoNotInstalledError` / `pdfinfo: not found`**: Poppler is missing. Run `sudo apt-get install poppler-utils` (Debian/Ubuntu) or `brew install poppler` (macOS).

## License

[MIT](LICENSE) © 2021-2026 Alireza Behtash
