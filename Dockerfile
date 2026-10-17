# Debian-based image: Tesseract and Poppler from the distribution's packages.
#
#   docker build -t tesseract-ocr-wrapper .
#   docker run --rm -v "$PWD:/data" tesseract-ocr-wrapper scan.pdf

FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app
COPY _sys.py requirements.txt ./
RUN python _sys.py && rm -rf /var/lib/apt/lists/*

COPY tesseract.py utils.py ocr.py ./

WORKDIR /data
ENTRYPOINT ["python", "/app/ocr.py"]
