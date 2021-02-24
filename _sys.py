"""
Installs the required packages from python env
and system-specific packages.
"""
import os
import sys
from pathlib import Path
from platform import system
from subprocess import check_call

if not os.environ.get("OMP_THREAD_LIMIT"):
    # Turn off tesseract's inner multithreading for performance reasons.
    os.environ["OMP_THREAD_LIMIT"] = "1"
    current_dir = Path.cwd()
    check_call(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "-r",
            str(Path("__file__").resolve().parent / "requirements.txt"),
        ]
    )
    commands = []
    if system() == "Linux":
        commands = [
            "sudo yum install poppler-utils",
            "sudo yum install autoconf automake libpng-devel libtiff-devel libtool pkgconfig.x86_64 libpng12-devel.x86_64 libjpeg-devel libtiff-devel.x86_64 zlib-devel.x86_64",
            "cd /tmp",
            "wget http://www.leptonica.org/source/leptonica-1.79.0.tar.gz",
            "tar -zxvf leptonica-1.79.0.tar.gz",
            "cd leptonica-1.79.0",
            "./configure --prefix=/usr/local/",
            "make",
            "sudo make install",
            "export PKG_CONFIG_PATH=/usr/local/leptonica-1.79.0/lib/pkgconfig",
            "cd /tmp",
            "wget https://codeload.github.com/tesseract-ocr/tesseract/tar.gz/4.1.1",
            "tar -zxvf 4.1.1",
            "cd tesseract-4.1.1",
            "./autogen.sh",
            "LIBLEPT_HEADERSDIR=/usr/local/lib ./configure --prefix=/usr/local/ --with-extra-libraries=/usr/local/lib",
            "autoreconf --force --install",
            "./configure",
            "make",
            "sudo make install",
            "sudo ldconfig",
            "cd /tmp",
            "wget https://github.com/tesseract-ocr/tessdata_fast/blob/master/eng.traineddata?raw=true",
            "sudo mv /tmp/eng.traineddata?raw=true /usr/local/share/tessdata/eng_fast.traineddata",
            f"cd {current_dir}",
        ]
    if commands:
        for command in commands:
            if command.startswith("cd "):
                os.chdir(Path(command))
            else:
                check_call(command, shell=True)
