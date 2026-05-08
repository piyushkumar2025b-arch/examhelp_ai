"""ocr_handler.py — Text extraction from images of study materials.

Uses pytesseract if available, otherwise falls back to a simpler
PIL-based approach for basic image validation.
"""

from __future__ import annotations
import io
import base64

# Bug #39: consolidated PIL imports — avoid importing twice under different names
try:
    from PIL import Image as PILImage
    _HAS_PIL = True
except ImportError:
    PILImage = None
    _HAS_PIL = False

try:
    import pytesseract
    _HAS_TESSERACT = _HAS_PIL  # pytesseract requires PIL to function
except ImportError:
    pytesseract = None
    _HAS_TESSERACT = False
    _HAS_PIL = False


def extract_text_from_image(img_bytes: bytes) -> str:
    """Extract text from an image using Tesseract OCR.
    
    Returns extracted text or an error message starting with 'Error:'.
    """
    if not _HAS_PIL:
        return "Error: Pillow not installed. Run: pip install pillow"

    ImageMod = PILImage

    try:
        image = ImageMod.open(io.BytesIO(img_bytes))
    except Exception as e:
        return f"Error: Could not open image — {e}"

    if _HAS_TESSERACT:
        try:
            text = pytesseract.image_to_string(image)
            cleaned = text.strip()
            if cleaned:
                return cleaned
            return "Error: No text detected in the image. Try a clearer photo."
        except Exception as e:
            return f"Error: OCR failed — {e}. Ensure Tesseract-OCR is installed on the system."
    else:
        return (
            "Error: pytesseract is not installed. "
            "Install it with: pip install pytesseract\n"
            "Also install Tesseract-OCR: https://github.com/tesseract-ocr/tesseract"
        )


def get_image_info(img_bytes: bytes) -> dict:
    """Returns basic metadata about the image."""
    ImageMod = PILImage
    if not ImageMod:
        return {}
    try:
        image = ImageMod.open(io.BytesIO(img_bytes))
        w, h = image.size
        return {
            "format": image.format or "unknown",
            "mode": image.mode,
            "width": w,
            "height": h,
            "megapixels": round((w * h) / 1_000_000, 2),
        }
    except Exception:
        return {}
