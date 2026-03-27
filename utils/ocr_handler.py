"""ocr_handler.py — Optical Character Recognition for study materials."""

from __future__ import annotations
import io
try:
    import pytesseract
    from PIL import Image
except ImportError:
    pytesseract = None
    Image = None

def extract_text_from_image(img_bytes: bytes) -> str:
    """Uses Tesseract to read text from an image (notes, textbooks)."""
    if not pytesseract or not Image:
        return "Error: pytesseract or PIL not installed. Use 'pip install pytesseract pillow'."
    
    try:
        image = Image.open(io.BytesIO(img_bytes))
        # Simple extraction for now
        text = pytesseract.image_to_string(image)
        return text.strip() or "No text detected in the image."
    except Exception as e:
        return f"OCR Error: {e}. Ensure Tesseract-OCR is installed on the system."

def get_image_info(img_bytes: bytes) -> dict:
    """Returns basic metadata about the image."""
    try:
        image = Image.open(io.BytesIO(img_bytes))
        w, h = image.size
        return {
            "format": image.format,
            "mode": image.mode,
            "width": w,
            "height": h,
            "megapixels": round((w * h) / 1_000_000, 2)
        }
    except Exception:
        return {}
