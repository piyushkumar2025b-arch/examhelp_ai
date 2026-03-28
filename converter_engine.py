"""
converter_engine.py — Universal File Converter Engine
Supports: PDF, DOCX, TXT, CSV, JSON, MD, HTML, XLSX, PNG/JPG, PPTX
"""
from __future__ import annotations
import io, os, base64, json, csv, re
from typing import Optional, Tuple

# ── Converters ────────────────────────────────────────────────────────────────

def _pdf_to_text(data: bytes) -> str:
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(data))
        return "\n\n".join(p.extract_text() or "" for p in reader.pages)
    except Exception as e:
        return f"[PDF extraction error: {e}]"

def _docx_to_text(data: bytes) -> str:
    try:
        from docx import Document
        doc = Document(io.BytesIO(data))
        return "\n".join(p.text for p in doc.paragraphs)
    except Exception as e:
        return f"[DOCX extraction error: {e}]"

def _excel_to_text(data: bytes) -> str:
    try:
        import openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
        out = []
        for sheet in wb.worksheets:
            out.append(f"=== Sheet: {sheet.title} ===")
            for row in sheet.iter_rows(values_only=True):
                row_vals = [str(c) if c is not None else "" for c in row]
                out.append("\t".join(row_vals))
        return "\n".join(out)
    except Exception as e:
        return f"[XLSX extraction error: {e}]"

def _csv_to_text(data: bytes) -> str:
    try:
        content = data.decode("utf-8", errors="replace")
        reader = csv.reader(io.StringIO(content))
        return "\n".join(",".join(row) for row in reader)
    except Exception as e:
        return f"[CSV extraction error: {e}]"

def _markdown_to_html(data: bytes) -> bytes:
    try:
        import markdown as md_lib
        html = md_lib.markdown(data.decode("utf-8", errors="replace"), extensions=["tables","fenced_code"])
    except ImportError:
        text = data.decode("utf-8", errors="replace")
        # basic fallback
        html = "<pre>" + text.replace("&","&amp;").replace("<","&lt;") + "</pre>"
    page = f"""<!DOCTYPE html><html><head><meta charset='utf-8'>
<style>body{{font-family:sans-serif;max-width:800px;margin:40px auto;line-height:1.6;}}
code{{background:#f4f4f4;padding:2px 6px;border-radius:4px;}}
pre{{background:#f4f4f4;padding:12px;border-radius:8px;overflow-x:auto;}}</style></head>
<body>{html}</body></html>"""
    return page.encode("utf-8")

def _text_to_pdf(data: bytes, title: str = "Document") -> bytes:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import cm
        from reportlab.pdfgen import canvas
        text = data.decode("utf-8", errors="replace")
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        w, h = A4
        y = h - 2*cm
        c.setFont("Helvetica-Bold", 14)
        c.drawString(2*cm, y, title)
        y -= 1*cm
        c.setFont("Helvetica", 10)
        for line in text.splitlines():
            if y < 2*cm:
                c.showPage()
                y = h - 2*cm
                c.setFont("Helvetica", 10)
            wrapped = [line[i:i+95] for i in range(0, max(1, len(line)), 95)] if len(line) > 95 else [line]
            for wl in wrapped:
                c.drawString(2*cm, y, wl)
                y -= 0.45*cm
        c.save()
        return buf.getvalue()
    except Exception as e:
        return f"PDF generation error: {e}".encode()

def _text_to_docx(data: bytes) -> bytes:
    try:
        from docx import Document
        text = data.decode("utf-8", errors="replace")
        doc = Document()
        for line in text.splitlines():
            doc.add_paragraph(line)
        buf = io.BytesIO()
        doc.save(buf)
        return buf.getvalue()
    except Exception as e:
        return f"DOCX error: {e}".encode()

def _text_to_html(data: bytes, title: str = "Document") -> bytes:
    text = data.decode("utf-8", errors="replace")
    safe = text.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
    html = f"""<!DOCTYPE html><html><head><meta charset='utf-8'><title>{title}</title>
<style>body{{font-family:'Segoe UI',sans-serif;max-width:860px;margin:48px auto;line-height:1.75;color:#1a1a2e;}}
pre{{background:#f5f5f5;padding:16px;border-radius:8px;white-space:pre-wrap;word-wrap:break-word;}}</style></head>
<body><h1>{title}</h1><pre>{safe}</pre></body></html>"""
    return html.encode("utf-8")

def _csv_to_html(data: bytes) -> bytes:
    try:
        content = data.decode("utf-8", errors="replace")
        rows = list(csv.reader(io.StringIO(content)))
        tbody = ""
        if rows:
            header = "".join(f"<th>{c}</th>" for c in rows[0])
            tbody = f"<thead><tr>{header}</tr></thead><tbody>"
            for row in rows[1:]:
                tbody += "<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>"
            tbody += "</tbody>"
        html = f"""<!DOCTYPE html><html><head><meta charset='utf-8'>
<style>body{{font-family:sans-serif;padding:24px;}}
table{{border-collapse:collapse;width:100%;}}
th,td{{border:1px solid #ddd;padding:8px 12px;}}
th{{background:#7c6af7;color:#fff;}}
tr:nth-child(even){{background:#f5f5fa;}}</style></head>
<body><table>{tbody}</table></body></html>"""
        return html.encode("utf-8")
    except Exception as e:
        return f"<p>Error: {e}</p>".encode()

def _json_to_html(data: bytes) -> bytes:
    try:
        obj = json.loads(data.decode("utf-8", errors="replace"))
        pretty = json.dumps(obj, indent=2, ensure_ascii=False)
        safe = pretty.replace("&","&amp;").replace("<","&lt;")
        html = f"""<!DOCTYPE html><html><head><meta charset='utf-8'>
<style>body{{font-family:monospace;padding:24px;background:#1a1a2e;color:#f0f0ff;}}
pre{{white-space:pre-wrap;word-wrap:break-word;font-size:14px;}}</style></head>
<body><pre>{safe}</pre></body></html>"""
        return html.encode("utf-8")
    except Exception as e:
        return f"<p>Error: {e}</p>".encode()

def _json_to_csv(data: bytes) -> bytes:
    try:
        obj = json.loads(data.decode("utf-8", errors="replace"))
        if isinstance(obj, list) and obj and isinstance(obj[0], dict):
            buf = io.StringIO()
            w = csv.DictWriter(buf, fieldnames=obj[0].keys())
            w.writeheader()
            w.writerows(obj)
            return buf.getvalue().encode("utf-8")
        else:
            return json.dumps(obj, indent=2).encode("utf-8")
    except Exception as e:
        return f"Error: {e}".encode()

def _csv_to_json(data: bytes) -> bytes:
    try:
        content = data.decode("utf-8", errors="replace")
        rows = list(csv.DictReader(io.StringIO(content)))
        return json.dumps(rows, indent=2, ensure_ascii=False).encode("utf-8")
    except Exception as e:
        return json.dumps({"error": str(e)}).encode()

def _html_to_text(data: bytes) -> bytes:
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(data, "html.parser")
        return soup.get_text(separator="\n").strip().encode("utf-8")
    except ImportError:
        clean = re.sub(r'<[^>]+>', ' ', data.decode("utf-8", errors="replace"))
        return re.sub(r'\s+', ' ', clean).strip().encode("utf-8")

# ── Conversion router ─────────────────────────────────────────────────────────

CONVERSIONS: dict[tuple, tuple] = {
    # (from, to): (function, mime, extension)
    ("pdf", "txt"):   (lambda d: _pdf_to_text(d).encode("utf-8"),      "text/plain",                  "txt"),
    ("pdf", "html"):  (lambda d: _text_to_html(_pdf_to_text(d).encode(),"PDF Export"), "text/html",   "html"),
    ("docx", "txt"):  (lambda d: _docx_to_text(d).encode("utf-8"),     "text/plain",                  "txt"),
    ("docx", "pdf"):  (lambda d: _text_to_pdf(_docx_to_text(d).encode(),"Document"),   "application/pdf","pdf"),
    ("docx", "html"): (lambda d: _text_to_html(_docx_to_text(d).encode(),"Document"),  "text/html",   "html"),
    ("txt", "pdf"):   (lambda d: _text_to_pdf(d, "Document"),          "application/pdf",             "pdf"),
    ("txt", "docx"):  (lambda d: _text_to_docx(d),                     "application/vnd.openxmlformats-officedocument.wordprocessingml.document","docx"),
    ("txt", "html"):  (lambda d: _text_to_html(d, "Document"),         "text/html",                   "html"),
    ("md",  "html"):  (lambda d: _markdown_to_html(d),                 "text/html",                   "html"),
    ("md",  "txt"):   (lambda d: d,                                     "text/plain",                  "txt"),
    ("md",  "pdf"):   (lambda d: _text_to_pdf(d, "Markdown Doc"),      "application/pdf",             "pdf"),
    ("csv", "json"):  (lambda d: _csv_to_json(d),                      "application/json",            "json"),
    ("csv", "html"):  (lambda d: _csv_to_html(d),                      "text/html",                   "html"),
    ("csv", "txt"):   (lambda d: _csv_to_text(d).encode("utf-8"),      "text/plain",                  "txt"),
    ("json","csv"):   (lambda d: _json_to_csv(d),                      "text/csv",                    "csv"),
    ("json","html"):  (lambda d: _json_to_html(d),                     "text/html",                   "html"),
    ("json","txt"):   (lambda d: d,                                     "text/plain",                  "txt"),
    ("xlsx","txt"):   (lambda d: _excel_to_text(d).encode("utf-8"),    "text/plain",                  "txt"),
    ("xlsx","csv"):   (lambda d: _excel_to_text(d).encode("utf-8"),    "text/csv",                    "csv"),
    ("html","txt"):   (lambda d: _html_to_text(d),                     "text/plain",                  "txt"),
}

def get_supported_formats() -> dict[str, list[str]]:
    sources: dict[str, list[str]] = {}
    for (src, dst) in CONVERSIONS:
        sources.setdefault(src, []).append(dst)
    return sources

def convert_file(data: bytes, from_fmt: str, to_fmt: str, filename: str = "file") -> Tuple[Optional[bytes], str, str, str]:
    """Returns (output_bytes, mime_type, extension, error_msg)"""
    key = (from_fmt.lower(), to_fmt.lower())
    if key not in CONVERSIONS:
        return None, "", "", f"Conversion from {from_fmt} → {to_fmt} is not supported."
    try:
        fn, mime, ext = CONVERSIONS[key]
        result = fn(data)
        return result, mime, ext, ""
    except Exception as e:
        return None, "", "", f"Conversion failed: {e}"
