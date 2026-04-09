"""pdf_handler.py — Extract text and metadata from uploaded PDF files.
FIX-10.1a/b/c: Intelligent chunking, metadata panel, chapter summarization.
"""

from __future__ import annotations
import io
import re
from typing import BinaryIO, List, Tuple

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None  # type: ignore


MAX_CHARS = 40_000   # increased limit for better coverage
MAX_PAGES_FULL = 80  # extract fully up to this many pages

# ── FIX-10.1a: Chunking constants ────────────────────────────────────────────
CHUNK_SIZE_CHARS = 8000    # ~2000 tokens approx (4 chars/token)
CHUNK_OVERLAP_CHARS = 800  # ~200 token overlap


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


def chunk_pdf_text(text: str) -> List[str]:
    """
    FIX-10.1a: Split PDF text into overlapping chunks for RAG-style Q&A.
    Each chunk is ~CHUNK_SIZE_CHARS with CHUNK_OVERLAP_CHARS overlap.
    Prevents context window overflow for large PDFs.
    """
    chunks: List[str] = []
    start = 0
    while start < len(text):
        end = min(start + CHUNK_SIZE_CHARS, len(text))
        chunks.append(text[start:end])
        if end >= len(text):
            break
        start += CHUNK_SIZE_CHARS - CHUNK_OVERLAP_CHARS
    return chunks


def find_relevant_chunks(question: str, chunks: List[str], top_k: int = 3) -> str:
    """
    FIX-10.1a: Find the top-k most relevant chunks using word-overlap scoring (TF-IDF-lite).
    Returns the concatenated top chunks as context for the AI call.
    """
    if not chunks:
        return ""
    q_words = set(re.sub(r'[^\w\s]', '', question.lower()).split())
    if not q_words:
        return "\n\n".join(chunks[:top_k])

    def score(chunk: str) -> float:
        chunk_words = set(re.sub(r'[^\w\s]', '', chunk.lower()).split())
        overlap = q_words & chunk_words
        return len(overlap) / max(len(q_words), 1)

    scored = sorted(enumerate(chunks), key=lambda x: score(x[1]), reverse=True)
    top_chunks = [chunks[i] for i, _ in scored[:top_k]]
    return "\n\n---\n\n".join(top_chunks)


def get_pdf_metadata(file: BinaryIO) -> dict:
    """
    FIX-10.1b: Return rich metadata dict from a PDF.
    Includes page count, file size, estimated reading time, language hint, and TOC.
    """
    if fitz is None:
        return {}
    try:
        data = file.read()
        doc = fitz.open(stream=data, filetype="pdf")
        meta = doc.metadata or {}
        meta["page_count"] = doc.page_count
        meta["file_size_kb"] = round(len(data) / 1024, 1)

        # Estimate word count and reading time (avg 250 wpm)
        total_words = 0
        for i, page in enumerate(doc):
            if i >= 10:
                break
            total_words += len(page.get_text().split())
        est_words = total_words * max(1, doc.page_count // max(1, min(10, doc.page_count)))
        meta["estimated_word_count"] = est_words
        meta["estimated_reading_min"] = max(1, round(est_words / 250))

        # Collect TOC if available
        toc = doc.get_toc()
        if toc:
            meta["toc"] = [(level, title) for level, title, _ in toc[:20]]

        return meta
    except Exception:
        return {}


def summarize_by_chapter(text: str) -> List[Tuple[str, str]]:
    """
    ADD-10.1c: Split text by [Page X] markers and identify heading-like sections.
    Returns [(section_title, section_text)] for chapter-level summarization.
    """
    # Split by page markers
    pages = re.split(r'\[Page \d+\]', text)
    pages = [p.strip() for p in pages if p.strip()]

    # Group pages into sections using heading heuristics
    sections: List[Tuple[str, str]] = []
    current_title = "Introduction"
    current_content: List[str] = []

    heading_pattern = re.compile(r'^(?:chapter|section|part|unit|\d+\.)\s+.{3,60}$', re.IGNORECASE)

    for page in pages:
        lines = page.splitlines()
        found_heading = False
        for line in lines[:5]:  # Only check first 5 lines for headings
            if heading_pattern.match(line.strip()):
                if current_content:
                    sections.append((current_title, "\n".join(current_content)))
                current_title = line.strip()
                current_content = []
                found_heading = True
                break
        current_content.append(page)

    if current_content:
        sections.append((current_title, "\n".join(current_content)))

    return sections[:20]  # Return at most 20 sections


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
            "reading_min": max(1, round(total_words / 250)),
        }
    except Exception:
        return {}



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