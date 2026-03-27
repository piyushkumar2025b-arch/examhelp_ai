import fitz  # PyMuPDF
import io


def extract_text_from_pdf(uploaded_file) -> str:
    """
    Extract all text from an uploaded PDF file (Streamlit UploadedFile object).
    Returns the extracted text as a string.
    """
    try:
        pdf_bytes = uploaded_file.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")

        text_parts = []
        for page_num, page in enumerate(doc, start=1):
            page_text = page.get_text("text")
            if page_text.strip():
                text_parts.append(f"[Page {page_num}]\n{page_text.strip()}")

        doc.close()

        if not text_parts:
            return "No readable text found in this PDF. It may be a scanned image-based PDF."

        full_text = "\n\n".join(text_parts)
        return full_text

    except Exception as e:
        return f"Error reading PDF: {str(e)}"


def get_pdf_metadata(uploaded_file) -> dict:
    """
    Returns basic metadata about the PDF.
    """
    try:
        pdf_bytes = uploaded_file.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        meta = {
            "pages": doc.page_count,
            "title": doc.metadata.get("title", uploaded_file.name),
            "author": doc.metadata.get("author", "Unknown"),
        }
        doc.close()
        return meta
    except Exception as e:
        return {"pages": "?", "title": uploaded_file.name, "author": "Unknown"}
