# License: GPLv3 Copyright: 2016, Kovid Goyal <kovid at kovidgoyal.net>
# Source: https://github.com/kovidgoyal/calibre/blob/master/src/calibre/utils/imghdr.py

from typing import Optional

HSIZE = 120


def what(file: str, h: bytes = None):
    """
    Recognize image file formats based on their first few bytes.
    """
    if h is None:
        with open(file, "rb") as f:
            h = f.read(HSIZE)
    if isinstance(h, bytes):
        h = memoryview(h)
    for tf in format_tests:
        res = tf(h)
        if res:
            return res
    # There exist some jpeg files with no headers, only the starting two bits
    # If we cannot identify as anything else, identify as jpeg.
    if h[:2] == b"\xff\xd8":
        return "jpeg"
    return None


# ---------------------------------#
# Subroutines per image file type #
# ---------------------------------#


format_tests = []


def format_test(f):
    format_tests.append(f)
    return f


@format_test
def jpeg(h: memoryview) -> Optional[str]:
    """
    JPEG data in JFIF format (Changed by Kovid to mimic the file utility,
    the original code was failing with some jpegs that included ICC_PROFILE
    data, for example: http://nationalpostnews.files.wordpress.com/2013/03/budget.jpeg?w=300&h=1571)
    """
    if h[6:10] in (b"JFIF", b"Exif"):
        return "jpeg"
    if h[:2] == b"\xff\xd8":
        q = h[:32].tobytes()
        if b"JFIF" in q or b"8BIM" in q:
            return "jpeg"


@format_test
def png(h: memoryview) -> Optional[str]:
    if h[:8] == b"\211PNG\r\n\032\n":
        return "png"


@format_test
def gif(h: memoryview) -> Optional[str]:
    """
    GIF ('87 and '89 variants)
    """
    if h[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"


@format_test
def tiff(h: memoryview) -> Optional[str]:
    """
    TIFF (can be in Motorola or Intel byte order)
    """
    if h[:2] in (b"MM", b"II"):
        if h[2:4] == b"\xbc\x01":
            return "jxr"
        return "tiff"


@format_test
def webp(h: memoryview) -> Optional[str]:
    if h[:4] == b"RIFF" and h[8:12] == b"WEBP":
        return "webp"


@format_test
def rgb(h: memoryview) -> Optional[str]:
    """
    SGI image library
    """
    if h[:2] == b"\001\332":
        return "rgb"


@format_test
def pbm(h: memoryview) -> Optional[str]:
    """
    PBM (portable bitmap)
    """
    if len(h) >= 3 and h[0] == b"P" and h[1] in b"14" and h[2] in b" \t\n\r":
        return "pbm"


@format_test
def pgm(h: memoryview) -> Optional[str]:
    """
    PGM (portable graymap)
    """
    if len(h) >= 3 and h[0] == b"P" and h[1] in b"25" and h[2] in b" \t\n\r":
        return "pgm"


@format_test
def ppm(h: memoryview) -> Optional[str]:
    """
    PPM (portable pixmap)
    """
    if len(h) >= 3 and h[0] == b"P" and h[1] in b"36" and h[2] in b" \t\n\r":
        return "ppm"


@format_test
def rast(h: memoryview) -> Optional[str]:
    """
    Sun raster file
    """
    if h[:4] == b"\x59\xA6\x6A\x95":
        return "rast"


@format_test
def xbm(h: memoryview) -> Optional[str]:
    """
    X bitmap (X10 or X11)
    """
    s = b"#define "
    if h[: len(s)] == s:
        return "xbm"


@format_test
def bmp(h: memoryview) -> Optional[str]:
    if h[:2] == b"BM":
        return "bmp"


@format_test
def emf(h: memoryview) -> Optional[str]:
    if h[:4] == b"\x01\0\0\0" and h[40:44] == b" EMF":
        return "emf"


@format_test
def jpeg2000(h: memoryview) -> Optional[str]:
    if h[:12] == b"\x00\x00\x00\x0cjP  \r\n\x87\n":
        return "jpeg2000"


@format_test
def svg(h: memoryview) -> Optional[str]:
    if h[:4] == b"<svg" or (
        h[:2] == b"<?" and h[2:5].tobytes().lower() == b"xml" and b"<svg" in h.tobytes()
    ):
        return "svg"
