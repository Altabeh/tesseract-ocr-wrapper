"""
A tesseract python wrapper that calls tesseract library under the hood.
"""

import ctypes
import ctypes.util
from platform import system

__all__ = ["Tesseract", "TesseractError"]

if system() in ["Darwin", "Windows"]:
    LIBNAME = "libtesseract"
else:
    LIBNAME = "tesseract"


class TesseractError(Exception):
    pass


class Tesseract(object):
    """
    The parent class ``Tesseract`` receives instructions/declarations of the tesseract library
    such as methods, arguments and their types written in C via the line `cls._lib = lib = ctypes.CDLL(lib_path)`
    in `setup_lib` method and allows python to manipulate them using the ctypes library.
    """

    _lib = None
    _api = None

    class TessBaseAPI(ctypes._Pointer):
        _type_ = type("_TessBaseAPI", (ctypes.Structure,), {})

    @classmethod
    def setup_lib(cls, lib_path=None):
        """
        Set up tesseract library.
        """
        if cls._lib is not None:
            return
        if lib_path is None:
            lib_path = ctypes.util.find_library(LIBNAME)
            if lib_path is None:
                raise TesseractError("tesseract library was not found")
        cls._lib = lib = ctypes.CDLL(lib_path)

        # Visit https://github.com/tesseract-ocr/tesseract/blob/master/include/tesseract/capi.h
        # to see what methods are available in the tesseract api and their arguments and type declarations.

        lib.TessBaseAPICreate.restype = cls.TessBaseAPI

        lib.TessBaseAPIDelete.restype = None  # void
        lib.TessBaseAPIDelete.argtypes = (cls.TessBaseAPI,)  # handle

        lib.TessBaseAPIInit3.argtypes = (
            cls.TessBaseAPI,  # handle
            ctypes.c_char_p,  # datapath
            ctypes.c_char_p,
        )  # language

        lib.TessBaseAPISetImage.restype = None
        lib.TessBaseAPISetImage.argtypes = (
            cls.TessBaseAPI,  # handle
            ctypes.c_void_p,  # imagedata
            ctypes.c_int,  # width
            ctypes.c_int,  # height
            ctypes.c_int,  # bytes_per_pixel
            ctypes.c_int,
        )  # bytes_per_line

        lib.TessBaseAPIGetUTF8Text.restype = ctypes.c_char_p
        lib.TessBaseAPIGetUTF8Text.argtypes = (cls.TessBaseAPI,)  # handle

    def __init__(self, language="eng_fast", datapath=None, lib_path=None):
        if self._lib is None:
            self.setup_lib(lib_path)
        self._api = self._lib.TessBaseAPICreate()
        if self._lib.TessBaseAPIInit3(
            self._api, datapath, bytes(language, encoding="utf-8")
        ):
            raise TesseractError("Initialization failed")

    def __del__(self):
        if not self._lib or not self._api:
            return
        if not getattr(self, "closed", False):
            self._lib.TessBaseAPIDelete(self._api)
            self.closed = True

    def _check_setup(self):
        """
        Check if the tesseract library is correctly read and configured.
        """
        if not self._lib:
            raise TesseractError("tesseract library failed to be configured")
        if not self._api:
            raise TesseractError("tesseract api failed to be created")

    def set_image(self, imagedata, width, height, bytes_per_pixel, bytes_per_line=None):
        """
        Call image object (`imagedata`) into TessBaseAPISetImage along with its
        metadata. `bytes_per_pixel` is 3 for RGB images.
        """
        self._check_setup()
        if bytes_per_line is None:
            bytes_per_line = width * bytes_per_pixel
        self._lib.TessBaseAPISetImage(
            self._api, imagedata, width, height, bytes_per_pixel, bytes_per_line
        )

    def set_variable(self, key, val):
        """
        Set a parameter on runtime for the tesseract api (e.g. `--key=val`).
        """
        self._check_setup()
        self._lib.TessBaseAPISetVariable(
            self._api, bytes(key, encoding="utf-8"), bytes(val, encoding="utf-8")
        )

    def get_utf8_text(self):
        """
        Extract utf8-encoded text by calling the tesseract api.
        """
        self._check_setup()
        return self._lib.TessBaseAPIGetUTF8Text(self._api)

    def get_text(self):
        """
        utf8-decode text returned by the method `get_utf8_text`.
        """
        utf8_text = self.get_utf8_text()
        if utf8_text:
            return utf8_text.decode("utf-8")
