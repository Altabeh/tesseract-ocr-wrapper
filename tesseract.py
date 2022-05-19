"""
A tesseract python wrapper that calls tesseract library under the hood.
"""

import ctypes
import ctypes.util
from enum import IntEnum

__all__ = ["Tesseract", "TesseractError"]

LIBNAME = "tesseract"

class PageSegMode(IntEnum):
    """
    Enum for page segmentation mode.
    """
    OSD_ONLY = 0,      # Orientation and script detection only.
    AUTO_OSD = 1,      # Automatic page segmentation with orientation and
                       # script detection. (OSD)
    AUTO_ONLY = 2,     # Automatic page segmentation, but no OSD, or OCR.
    AUTO = 3,          # Fully automatic page segmentation, but no OSD.
    SINGLE_COLUMN = 4, # Assume a single column of text of variable sizes.
    SINGLE_BLOCK_VERT_TEXT = 5, # Assume a single uniform block of
                                # vertically aligned text.
    SINGLE_BLOCK = 6, # Assume a single uniform block of text. (Default.)
    SINGLE_LINE = 7,  # Treat the image as a single text line.
    SINGLE_WORD = 8,  # Treat the image as a single word.
    CIRCLE_WORD = 9,  # Treat the image as a single word in a circle.
    SINGLE_CHAR = 10, # Treat the image as a single character.
    SPARSE_TEXT = 11, # Find as much text as possible in no particular order.
    SPARSE_TEXT_OSD = 12, # Sparse text with orientation and script det.
    RAW_LINE = 13, # Treat the image as a single text line, bypassing
                   # hacks that are Tesseract-specific.

def to_char_p(string: str):
    """Convert to ctypes pointer"""
    return ctypes.create_string_buffer(bytes(string, encoding="utf-8"))


LP_c_char = ctypes.POINTER(ctypes.c_char)

def to_char_p_p(strings: list):
    """Convert list of strings to list of ctypes pointers"""
    vec = (LP_c_char * len(strings))()
    for i, s in enumerate(strings):
        vec[i] = to_char_p(s)
    return vec

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
                raise TesseractError(f"{LIBNAME} library was not found")
        cls._lib = lib = ctypes.CDLL(lib_path)

        # Visit https://github.com/tesseract-ocr/tesseract/blob/master/include/tesseract/capi.h
        # to see what methods are available in the tesseract api and their arguments and type declarations.

        lib.TessBaseAPICreate.restype = cls.TessBaseAPI

        lib.TessBaseAPIDelete.restype = None  # void
        lib.TessBaseAPIDelete.argtypes = (cls.TessBaseAPI,)  # handle

        lib.TessBaseAPIInit3.argtypes = (
            cls.TessBaseAPI,  # handle
            ctypes.c_char_p,  # datapath
            ctypes.c_char_p,  # language
        )

        lib.TessBaseAPIInit4.argtypes = (
            cls.TessBaseAPI,  # handle
            ctypes.c_char_p,  # datapath
            ctypes.c_char_p,  # language
            ctypes.c_int, # mode
            ctypes.POINTER(LP_c_char), # configs
            ctypes.c_int, # configs_size,
            ctypes.POINTER(LP_c_char), # vars_vec
            ctypes.POINTER(LP_c_char), # vars_values
            ctypes.c_size_t, # vars_vec_size,
            ctypes.c_int # set_only_non_debug_params (bool)
        )

        lib.TessBaseAPISetImage.restype = None
        lib.TessBaseAPISetImage.argtypes = (
            cls.TessBaseAPI,  # handle
            ctypes.c_void_p,  # imagedata
            ctypes.c_int,  # width
            ctypes.c_int,  # height
            ctypes.c_int,  # bytes_per_pixel
            ctypes.c_int,  # bytes_per_line
        )

        lib.TessBaseAPISetPageSegMode.restype = None
        lib.TessBaseAPISetPageSegMode.argtypes = (
            cls.TessBaseAPI,  # handle
            ctypes.c_int,  # mode
        )

        lib.TessBaseAPIGetUTF8Text.restype = ctypes.c_char_p
        lib.TessBaseAPIGetUTF8Text.argtypes = (cls.TessBaseAPI,)  # handle

    def __init__(self, language="eng", datapath=None, lib_path=None):
        if self._lib is None:
            self.setup_lib(lib_path)
        if isinstance(datapath, str):
            datapath = bytes(datapath, encoding="utf-8")
        self._api = self._lib.TessBaseAPICreate()
        if self._lib.TessBaseAPIInit3(
            self._api, datapath, bytes(language, encoding="utf-8")
        ):
        # vars_vec = to_char_p_p(["load_system_dawg", "load_freq_dawg"])
        # vars_values = to_char_p_p(["F", "F"])
        # if self._lib.TessBaseAPIInit4(
        #     self._api, datapath, bytes(language, encoding="utf-8"),
        #     1, # OEM_TESSERACT_LSTM_COMBINED --TessOcrEngineMode.OEM_DEFAULT,
        #     None, 0, # configs
        #     vars_vec, vars_values, len(vars_vec), # vars
        #     0, # bool set_only_non_debug_params
        # ):
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

    def set_image(self, imagedata, width: int, height: int, bytes_per_pixel: int, bytes_per_line: int = 0):
        """
        Call image object (`imagedata`) into TessBaseAPISetImage along with its
        metadata. `bytes_per_pixel` is 3 for RGB images.
        """
        self._check_setup()
        if not bytes_per_line:
            bytes_per_line = width * bytes_per_pixel
        self._lib.TessBaseAPISetImage(
            self._api, imagedata, width, height, bytes_per_pixel, bytes_per_line
        )

    def set_psm(self, mode: int):
        """
        Set the page segmentation mode.
        """
        self._check_setup()
        self._lib.TessBaseAPISetPageSegMode(self._api, mode)

    def set_variable(self, key: str, val: str):
        """
        Set a parameter on runtime for the tesseract api (e.g. `--key=val`).
        """
        self._check_setup()
        self._lib.TessBaseAPISetVariable(
            self._api, bytes(key, encoding="utf-8"), bytes(val, encoding="utf-8")
        )

    def get_utf8_text(self) -> bytearray:
        """
        Extract utf8-encoded text by calling the tesseract api.
        """
        self._check_setup()
        return self._lib.TessBaseAPIGetUTF8Text(self._api)

    def get_text(self) -> str:
        """
        utf8-decode text returned by the method `get_utf8_text`.
        """
        utf8_text = self.get_utf8_text()
        if utf8_text:
            return utf8_text.decode("utf-8")
