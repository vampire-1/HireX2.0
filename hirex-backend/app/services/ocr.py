import os
from typing import Optional
from ..config import settings

try:
    import pytesseract
    from PIL import Image
except Exception:
    pytesseract = None
    Image = None

try:
    from pdf2image import convert_from_path
except Exception:
    convert_from_path = None


def _configure_tesseract():
    if pytesseract and settings.TESSERACT_CMD:
        pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD


def ocr_image_path(img_path: str) -> str:
    if not pytesseract or not Image:
        return ""
    _configure_tesseract()
    try:
        im = Image.open(img_path)
        return pytesseract.image_to_string(im) or ""
    except Exception:
        return ""


def ocr_pdf_path(pdf_path: str, max_pages: int = 25) -> str:
    if not pytesseract or not convert_from_path:
        return ""
    _configure_tesseract()
    try:
        images = convert_from_path(pdf_path, dpi=200, first_page=1, last_page=max_pages,
                                   poppler_path=settings.POPPLER_PATH or None)
        chunks = []
        for im in images:
            t = pytesseract.image_to_string(im) or ""
            if t.strip(): chunks.append(t)
        return "\n".join(chunks)
    except Exception:
        return ""
