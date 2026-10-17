"""
Install the system and Python dependencies needed by tesseract-ocr-wrapper.

Supported platforms:

* Debian-based Linux (Debian, Ubuntu, Mint, Pop!_OS, ...): installs Tesseract
  and Poppler from the distribution's packages with ``apt-get``.
* RHEL-based Linux (RHEL/UBI, Rocky, AlmaLinux, CentOS Stream, Fedora, ...):
  installs build tools with ``dnf``/``yum`` and compiles Leptonica and
  Tesseract from source.
* macOS: installs Tesseract and Poppler with Homebrew.

Usage::

    python _sys.py              # install everything
    python _sys.py --dry-run    # print the commands without running them
    python _sys.py --skip-pip   # only install system packages
"""
import argparse
import ctypes.util
import os
import shlex
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path
from platform import system

REPO_DIR = Path(__file__).resolve().parent

APT_PACKAGES = [
    "tesseract-ocr",
    "tesseract-ocr-eng",
    "poppler-utils",
]

RHEL_PACKAGES = [
    "poppler-utils",
    "autoconf",
    "automake",
    "libtool",
    "pkgconf-pkg-config",
    "make",
    "gcc-c++",
    "libpng-devel",
    "libjpeg-turbo-devel",
    "libtiff-devel",
    "libwebp-devel",
    "zlib-devel",
]

LEPTONICA_VERSION = "1.87.0"
LEPTONICA_URL = (
    "https://github.com/DanBloomberg/leptonica/releases/download/"
    f"{LEPTONICA_VERSION}/leptonica-{LEPTONICA_VERSION}.tar.gz"
)
TESSERACT_VERSION = "5.5.3"
TESSERACT_URL = (
    "https://github.com/tesseract-ocr/tesseract/archive/refs/tags/"
    f"{TESSERACT_VERSION}.tar.gz"
)
ENG_TRAINEDDATA_URL = (
    "https://github.com/tesseract-ocr/tessdata_fast/raw/main/eng.traineddata"
)
PREFIX = "/usr/local"


class Installer:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.sudo = self._sudo_prefix()

    def _sudo_prefix(self) -> list:
        if os.name != "posix" or os.geteuid() == 0:
            return []
        if shutil.which("sudo") is None and not self.dry_run:
            sys.exit("error: root privileges are required; run as root or install sudo")
        return ["sudo"]

    def run(self, cmd: list, cwd=None, env=None, root=False):
        if root:
            cmd = self.sudo + cmd
        location = f"(in {cwd}) " if cwd else ""
        print(f"+ {location}{shlex.join(str(c) for c in cmd)}", flush=True)
        if not self.dry_run:
            subprocess.check_call(cmd, cwd=cwd, env=env)

    def download(self, url: str, dest: Path):
        print(f"+ download {url} -> {dest}", flush=True)
        if not self.dry_run:
            with urllib.request.urlopen(url) as resp, open(dest, "wb") as out:
                shutil.copyfileobj(resp, out)

    def extract(self, archive: Path, dest: Path) -> Path:
        """Extract a tarball and return the top-level directory it contains."""
        print(f"+ extract {archive} -> {dest}", flush=True)
        if self.dry_run:
            return dest / archive.name.replace(".tar.gz", "")
        with tarfile.open(archive) as tar:
            top = tar.getnames()[0].split("/")[0]
            if hasattr(tarfile, "data_filter"):
                tar.extractall(dest, filter="data")
            else:
                tar.extractall(dest)
        return dest / top


def read_os_release(path: str = "/etc/os-release") -> dict:
    info = {}
    try:
        with open(path) as fh:
            for line in fh:
                key, sep, value = line.strip().partition("=")
                if sep:
                    info[key] = value.strip('"')
    except OSError:
        pass
    return info


def detect_platform() -> str:
    """Return one of ``debian``, ``rhel``, ``macos`` or ``unsupported``."""
    if system() == "Darwin":
        return "macos"
    if system() != "Linux":
        return "unsupported"
    info = read_os_release()
    ids = {info.get("ID", "")} | set(info.get("ID_LIKE", "").split())
    if ids & {"debian", "ubuntu"} or shutil.which("apt-get"):
        return "debian"
    if ids & {"rhel", "centos", "fedora", "amzn"} or shutil.which("dnf") or shutil.which("yum"):
        return "rhel"
    return "unsupported"


def install_debian(inst: Installer):
    inst.run(["apt-get", "update"], root=True)
    inst.run(
        [
            "env",
            "DEBIAN_FRONTEND=noninteractive",
            "apt-get",
            "install",
            "-y",
            "--no-install-recommends",
            *APT_PACKAGES,
        ],
        root=True,
    )


def install_rhel(inst: Installer):
    pkg_manager = "dnf" if shutil.which("dnf") else "yum"
    inst.run([pkg_manager, "install", "-y", *RHEL_PACKAGES], root=True)

    build_env = dict(os.environ, PKG_CONFIG_PATH=f"{PREFIX}/lib/pkgconfig")
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)

        archive = tmp / f"leptonica-{LEPTONICA_VERSION}.tar.gz"
        inst.download(LEPTONICA_URL, archive)
        src = inst.extract(archive, tmp)
        inst.run(["./configure", f"--prefix={PREFIX}"], cwd=src)
        inst.run(["make", f"-j{os.cpu_count() or 1}"], cwd=src)
        inst.run(["make", "install"], cwd=src, root=True)

        archive = tmp / f"tesseract-{TESSERACT_VERSION}.tar.gz"
        inst.download(TESSERACT_URL, archive)
        src = inst.extract(archive, tmp)
        inst.run(["./autogen.sh"], cwd=src, env=build_env)
        inst.run(["./configure", f"--prefix={PREFIX}"], cwd=src, env=build_env)
        inst.run(["make", f"-j{os.cpu_count() or 1}"], cwd=src, env=build_env)
        inst.run(["make", "install"], cwd=src, root=True)

        # /usr/local/lib is not on the default linker path on RHEL-based systems.
        inst.run(
            ["sh", "-c", f"echo {PREFIX}/lib > /etc/ld.so.conf.d/usr-local-lib.conf"],
            root=True,
        )
        inst.run(["ldconfig"], root=True)

        traineddata = tmp / "eng.traineddata"
        inst.download(ENG_TRAINEDDATA_URL, traineddata)
        inst.run(
            [
                "install",
                "-D",
                "-m",
                "644",
                str(traineddata),
                f"{PREFIX}/share/tessdata/eng.traineddata",
            ],
            root=True,
        )


def install_macos(inst: Installer):
    if shutil.which("brew") is None and not inst.dry_run:
        sys.exit("error: Homebrew is required on macOS; see https://brew.sh")
    inst.run(["brew", "install", "tesseract", "poppler"])


def install_python_requirements(inst: Installer):
    if sys.prefix == sys.base_prefix:
        print(
            "warning: not running inside a virtual environment; pip may refuse to "
            "install into the system Python (see README)",
            file=sys.stderr,
        )
    inst.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "-r",
            str(REPO_DIR / "requirements.txt"),
        ]
    )


def verify():
    ok = True
    if shutil.which("pdfinfo") is None:
        print("check: pdfinfo (poppler-utils) NOT found on PATH")
        ok = False
    else:
        print("check: pdfinfo found")
    lib = ctypes.util.find_library("tesseract")
    if lib is None:
        print("check: libtesseract NOT found by the dynamic loader")
        ok = False
    else:
        print(f"check: libtesseract found ({lib})")
    return ok


def main():
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument(
        "--dry-run", action="store_true", help="print commands without running them"
    )
    parser.add_argument(
        "--skip-pip", action="store_true", help="do not install Python requirements"
    )
    parser.add_argument(
        "--skip-system", action="store_true", help="do not install system packages"
    )
    args = parser.parse_args()

    inst = Installer(dry_run=args.dry_run)
    platform = detect_platform()
    print(f"Detected platform: {platform}")

    if not args.skip_system:
        if platform == "debian":
            install_debian(inst)
        elif platform == "rhel":
            install_rhel(inst)
        elif platform == "macos":
            install_macos(inst)
        else:
            sys.exit(
                "error: unsupported platform; install Tesseract (with libtesseract) "
                "and poppler-utils manually, then re-run with --skip-system"
            )

    if not args.skip_pip:
        install_python_requirements(inst)

    if not args.dry_run:
        if not verify():
            sys.exit(1)
        print("All dependencies are installed.")


if __name__ == "__main__":
    main()
