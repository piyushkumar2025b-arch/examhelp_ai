"""pdf_handler.py — Extract text and metadata from uploaded PDF files."""

from __future__ import annotations
import io
from typing import BinaryIO

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None  # type: ignore


MAX_CHARS = 15_000


def extract_text_from_pdf(file: BinaryIO) -> str:
    """Return extracted text from a PDF file object (max MAX_CHARS chars)."""
    if fitz is None:
        return "Error: PyMuPDF not installed. Run: pip install PyMuPDF"
    try:
        data = file.read()
        doc = fitz.open(stream=data, filetype="pdf")
        parts: list[str] = []
        for page in doc:
            parts.append(page.get_text())
        full_text = "\n".join(parts)
        return full_text[:MAX_CHARS]
    except Exception as e:
        return f"Error extracting PDF text: {e}"


def get_pdf_metadata(file: BinaryIO) -> dict:
    """Return basic metadata dict from a PDF."""
    if fitz is None:
        return {}
    try:
        data = file.read()
        doc = fitz.open(stream=data, filetype="pdf")
        meta = doc.metadata or {}
        meta["page_count"] = doc.page_count
        return meta
    except Exception:
        return {}
