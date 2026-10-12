"""
Installs the required packages from python env
and system-specific packages.
"""
import os
import sys
from pathlib import Path
from platform import system,freedesktop_os_release 
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
    if system() == "Linux" and  freedesktop_os_release()['ID_LIKE'] == 'debian':
        commands = [
        "sudo apt update",
        "sudo apt install -y tesseract-ocr tesseract-ocr-eng libleptonica-dev poppler-utils",
        "sudo ldconfig",
        ]
    if commands:
        for command in commands:
            if command.startswith("cd "):
                os.chdir(command[3:].strip())
            else:
                check_call(command, shell=True)
