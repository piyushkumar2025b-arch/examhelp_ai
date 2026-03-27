"""pdf_handler.py — Extract text and metadata from uploaded PDF files."""

from __future__ import annotations
import io
from typing import BinaryIO

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None  # type: ignore


MAX_CHARS = 40_000   # increased limit for better coverage
MAX_PAGES_FULL = 80  # extract fully up to this many pages


def extract_text_from_pdf(file: BinaryIO) -> str:
    """
    Return extracted text from a PDF file object.
    Includes page markers so the AI knows where content comes from.
    Returns up to MAX_CHARS characters.
    """
    if fitz is None:
        return "Error: PyMuPDF not installed. Run: pip install PyMuPDF"
    try:
        data = file.read()
        doc = fitz.open(stream=data, filetype="pdf")
        parts: list[str] = []
        total_pages = doc.page_count
        pages_to_read = min(total_pages, MAX_PAGES_FULL)

        for i, page in enumerate(doc):
            if i >= pages_to_read:
                parts.append(f"\n[... {total_pages - pages_to_read} more pages not shown due to length limit ...]\n")
                break
            page_text = page.get_text().strip()
            if page_text:
                parts.append(f"[Page {i+1}]\n{page_text}")

        full_text = "\n\n".join(parts)
        return full_text[:MAX_CHARS]
    except Exception as e:
        return f"Error extracting PDF text: {e}"


def get_pdf_metadata(file: BinaryIO) -> dict:
    """Return rich metadata dict from a PDF."""
    if fitz is None:
        return {}
    try:
        data = file.read()
        doc = fitz.open(stream=data, filetype="pdf")
        meta = doc.metadata or {}
        meta["page_count"] = doc.page_count

        # Estimate word count
        word_count = 0
        for i, page in enumerate(doc):
            if i >= 10:
                break
            word_count += len(page.get_text().split())
        meta["estimated_word_count"] = word_count * max(1, doc.page_count // max(1, min(10, doc.page_count)))

        # Collect TOC if available
        toc = doc.get_toc()
        if toc:
            meta["toc"] = [(level, title) for level, title, _ in toc[:20]]

        return meta
    except Exception:
        return {}


def get_pdf_summary_stats(file: BinaryIO) -> dict:
    """Return a stats summary suitable for display in the UI."""
    if fitz is None:
        return {}
    try:
        data = file.read()
        doc = fitz.open(stream=data, filetype="pdf")
        meta = doc.metadata or {}

        total_words = 0
        has_images = False
        for page in doc:
            total_words += len(page.get_text().split())
            if page.get_images():
                has_images = True

        return {
            "pages": doc.page_count,
            "words": total_words,
            "title": meta.get("title", ""),
            "author": meta.get("author", ""),
            "has_images": has_images,
            "toc_entries": len(doc.get_toc()),
        }
    except Exception:
        return {}