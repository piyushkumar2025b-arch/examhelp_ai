"""
file_viewer_addon.py — Universal File Viewer (No AI)
Supports: Images, Text/Code, PDF, CSV, JSON, Excel, Audio, Video, Markdown
Pure viewer — no AI processing whatsoever.
"""
import streamlit as st
import os

VIEWER_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Rajdhani:wght@400;600;700&family=Space+Mono&display=swap');

.fv-hero {
    background: linear-gradient(135deg,rgba(15,23,42,0.97),rgba(20,10,40,0.95));
    border: 1px solid rgba(99,102,241,0.2);
    border-radius: 22px; padding: 28px 32px; margin-bottom: 20px;
    position: relative; overflow: hidden;
}
.fv-hero::after {
    content:''; position:absolute; top:-1px; left:8%; right:8%; height:1px;
    background: linear-gradient(90deg,transparent,rgba(99,102,241,0.5),transparent);
}
.fv-title {
    font-family:'Rajdhani',sans-serif; font-size:2rem; font-weight:700;
    color:#fff; margin-bottom:4px;
}
.fv-sub { font-size:.9rem; color:rgba(255,255,255,0.4); }

.fv-card {
    background: rgba(15,23,42,0.75);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 16px; padding: 20px 22px; margin-bottom: 14px;
}
.fv-label {
    font-family:'Space Mono',monospace; font-size:9px; letter-spacing:3px;
    color:rgba(255,255,255,0.3); text-transform:uppercase; margin-bottom:8px;
}
.fv-badge {
    display:inline-block; padding:3px 12px; border-radius:100px;
    font-family:'Space Mono',monospace; font-size:10px; font-weight:700;
    background:rgba(99,102,241,0.12); border:1px solid rgba(99,102,241,0.25);
    color:#a5b4fc; margin-right:6px; margin-bottom:4px;
}
.fv-info-row {
    display:flex; flex-wrap:wrap; gap:8px; margin-top:10px;
    font-family:'Rajdhani',sans-serif; font-size:.85rem; color:rgba(255,255,255,0.5);
}
.fv-code-wrap {
    background: #0d1117; border:1px solid rgba(255,255,255,0.06);
    border-radius:12px; padding:18px; overflow-x:auto;
    font-family:'JetBrains Mono',monospace; font-size:.82rem;
    color:#e6edf3; line-height:1.7; white-space:pre-wrap; word-break:break-all;
    max-height:600px; overflow-y:auto;
}
</style>
"""

# ── Supported types ────────────────────────────────────────────────────────────
IMAGE_TYPES   = ["png","jpg","jpeg","gif","bmp","webp","svg","ico","tiff"]
TEXT_TYPES    = ["txt","md","py","js","ts","css","html","xml","yaml","yml",
                 "toml","ini","cfg","env","sh","bat","sql","log","rst","tex"]
CODE_LANG_MAP = {
    "py":"python","js":"javascript","ts":"typescript","html":"html",
    "css":"css","sql":"sql","sh":"bash","bat":"batch","md":"markdown",
    "xml":"xml","yaml":"yaml","yml":"yaml","toml":"toml","json":"json",
    "rst":"rst","tex":"latex","ini":"ini","cfg":"ini","log":"text",
    "txt":"text","env":"text",
}
CSV_TYPES     = ["csv","tsv"]
JSON_TYPES    = ["json","jsonl"]
PDF_TYPES     = ["pdf"]
AUDIO_TYPES   = ["mp3","wav","ogg","flac","m4a"]
VIDEO_TYPES   = ["mp4","webm","ogv","mov"]
EXCEL_TYPES   = ["xlsx","xls"]
DOCX_TYPES    = ["docx","doc"]
ALL_SUPPORTED = IMAGE_TYPES + TEXT_TYPES + CSV_TYPES + JSON_TYPES + \
                PDF_TYPES + AUDIO_TYPES + VIDEO_TYPES + EXCEL_TYPES + DOCX_TYPES


def _fmt_size(n: int) -> str:
    if n < 1024:       return f"{n} B"
    if n < 1024**2:    return f"{n/1024:.1f} KB"
    if n < 1024**3:    return f"{n/1024**2:.1f} MB"
    return f"{n/1024**3:.2f} GB"


def _render_image(file):
    st.image(file, use_container_width=True)


def _render_text(file, ext: str):
    try:
        raw = file.read().decode("utf-8", errors="replace")
    except Exception as e:
        st.error(f"Cannot read file: {e}"); return
    lang = CODE_LANG_MAP.get(ext, "text")
    lines = raw.count("\n") + 1
    words = len(raw.split())
    col1, col2, col3 = st.columns(3)
    col1.metric("Lines", f"{lines:,}")
    col2.metric("Words", f"{words:,}")
    col3.metric("Chars", f"{len(raw):,}")
    st.markdown(f"```{lang}\n{raw[:50000]}\n```")
    if len(raw) > 50000:
        st.caption(f"⚠️ Showing first 50,000 chars of {len(raw):,} total.")
    st.download_button("⬇️ Download File", raw.encode(), file_name=file.name,
                       use_container_width=True, key="fv_dl_text")


def _render_csv(file, ext: str):
    try:
        import pandas as pd, io
        sep = "\t" if ext == "tsv" else ","
        df = pd.read_csv(io.BytesIO(file.read()), sep=sep)
        st.markdown(f"**{df.shape[0]:,} rows × {df.shape[1]:,} columns**")
        # Search / filter
        search = st.text_input("🔍 Filter rows (case-insensitive):", key="fv_csv_search", placeholder="type to filter…")
        if search:
            mask = df.astype(str).apply(lambda col: col.str.contains(search, case=False, na=False)).any(axis=1)
            df = df[mask]
            st.caption(f"Showing {len(df):,} matching rows")
        st.dataframe(df, use_container_width=True, height=500)
        st.download_button("⬇️ Download CSV", file.getvalue() if hasattr(file, 'getvalue') else b"",
                           file_name=file.name, mime="text/csv", use_container_width=True, key="fv_dl_csv")
    except Exception as e:
        st.error(f"CSV error: {e}")


def _render_json(file):
    try:
        import json
        raw = file.read().decode("utf-8", errors="replace")
        data = json.loads(raw)
        pretty = json.dumps(data, indent=2, ensure_ascii=False)
        st.markdown(f"**Type:** `{type(data).__name__}` · **Size:** {_fmt_size(len(raw))}")
        if isinstance(data, list):
            st.caption(f"Array with {len(data):,} items")
        elif isinstance(data, dict):
            st.caption(f"Object with {len(data):,} keys")
        st.code(pretty[:30000], language="json")
        if len(pretty) > 30000:
            st.caption("⚠️ Truncated at 30,000 chars")
    except json.JSONDecodeError:
        # JSONL fallback
        file.seek(0)
        lines = file.read().decode("utf-8", errors="replace").strip().split("\n")
        st.warning(f"Not valid JSON — showing as {len(lines)} JSONL lines")
        for i, line in enumerate(lines[:100], 1):
            st.text(f"[{i}] {line[:200]}")


def _render_pdf(file):
    import base64
    data = file.read()
    b64 = base64.b64encode(data).decode()
    st.markdown(f"""
    <iframe src="data:application/pdf;base64,{b64}"
        width="100%" height="800px"
        style="border:1px solid rgba(255,255,255,0.1);border-radius:12px;">
    </iframe>
    """, unsafe_allow_html=True)
    st.download_button("⬇️ Download PDF", data, file_name=file.name,
                       mime="application/pdf", use_container_width=True, key="fv_dl_pdf")


def _render_audio(file):
    st.audio(file)
    st.caption(f"🎵 {file.name} — use the player above")


def _render_video(file):
    st.video(file)
    st.caption(f"🎬 {file.name} — use the player above")


def _render_excel(file):
    try:
        import pandas as pd, io
        xl = pd.ExcelFile(io.BytesIO(file.read()))
        sheets = xl.sheet_names
        st.markdown(f"**Sheets:** {', '.join(f'`{s}`' for s in sheets)}")
        selected = st.selectbox("Select sheet:", sheets, key="fv_xl_sheet")
        df = xl.parse(selected)
        st.markdown(f"**{df.shape[0]:,} rows × {df.shape[1]:,} columns**")
        st.dataframe(df, use_container_width=True, height=500)
    except Exception as e:
        st.error(f"Excel error: {e}. Install: `pip install openpyxl`")


def _render_docx(file):
    try:
        from docx import Document
        import io
        doc = Document(io.BytesIO(file.read()))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        st.markdown(f"**Paragraphs:** {len(paragraphs):,}")
        full_text = "\n\n".join(paragraphs)
        st.text_area("Document Content", full_text[:20000], height=600,
                     label_visibility="collapsed", key="fv_docx_view")
        if len(full_text) > 20000:
            st.caption("⚠️ Showing first 20,000 chars")
        st.download_button("⬇️ Download", file.getvalue() if hasattr(file,'getvalue') else b"",
                           file_name=file.name, use_container_width=True, key="fv_dl_docx")
    except ImportError:
        st.error("Install python-docx: `pip install python-docx`")
    except Exception as e:
        st.error(f"DOCX error: {e}")


# ── Main page ─────────────────────────────────────────────────────────────────
def render_file_viewer_page():
    """Main File Viewer page — no AI, pure file rendering."""
    st.markdown(VIEWER_CSS, unsafe_allow_html=True)

    # Hero
    st.markdown("""
    <div class="fv-hero">
        <div class="fv-title">📂 Universal File Viewer</div>
        <div class="fv-sub">Open & view any file directly in your browser — no AI, no uploads to servers.</div>
    </div>
    """, unsafe_allow_html=True)

    # Supported types pills
    st.markdown('<div class="fv-label">Supported Formats</div>', unsafe_allow_html=True)
    badges = ""
    for label, types in [
        ("🖼️ Images", IMAGE_TYPES), ("📄 Text/Code", TEXT_TYPES),
        ("📊 CSV/TSV", CSV_TYPES), ("🔧 JSON", JSON_TYPES),
        ("📕 PDF", PDF_TYPES), ("🎵 Audio", AUDIO_TYPES),
        ("🎬 Video", VIDEO_TYPES), ("📊 Excel", EXCEL_TYPES),
        ("📝 Word", DOCX_TYPES),
    ]:
        badges += f'<span class="fv-badge">{label}</span>'
    st.markdown(badges, unsafe_allow_html=True)
    st.markdown("")

    # File uploader — accept all listed types
    all_ext = [f".{e}" for e in ALL_SUPPORTED]
    uploaded = st.file_uploader(
        "Choose any file to view",
        type=ALL_SUPPORTED,
        key="fv_uploader",
        label_visibility="collapsed",
        help="Drag & drop or click to browse. Max 200 MB."
    )

    if not uploaded:
        st.markdown("""
        <div class="fv-card" style="text-align:center;padding:40px;">
            <div style="font-size:3rem;margin-bottom:12px;">📂</div>
            <div style="font-family:'Rajdhani',sans-serif;font-size:1.1rem;color:rgba(255,255,255,0.5);">
                Drop any file here to view it instantly.<br>
                <span style="font-size:.85rem;color:rgba(255,255,255,0.25);">
                    Images · PDFs · Code · CSV · Excel · Word · Audio · Video
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    # ── File info bar ──────────────────────────────────────────────────────────
    ext = uploaded.name.rsplit(".", 1)[-1].lower() if "." in uploaded.name else ""
    size_bytes = uploaded.size
    mime = uploaded.type or "application/octet-stream"

    st.markdown(f"""
    <div class="fv-card">
        <div class="fv-label">File Information</div>
        <div style="font-family:'Rajdhani',sans-serif;font-size:1.1rem;font-weight:700;color:#fff;margin-bottom:8px;">
            📄 {uploaded.name}
        </div>
        <div class="fv-info-row">
            <span>📦 <strong>{_fmt_size(size_bytes)}</strong></span>
            <span>🏷️ .{ext.upper()}</span>
            <span>🔖 {mime}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Route to correct renderer ──────────────────────────────────────────────
    st.markdown('<div class="fv-label">File Preview</div>', unsafe_allow_html=True)

    if ext in IMAGE_TYPES:
        _render_image(uploaded)

    elif ext in TEXT_TYPES:
        _render_text(uploaded, ext)

    elif ext in CSV_TYPES:
        _render_csv(uploaded, ext)

    elif ext in JSON_TYPES:
        _render_json(uploaded)

    elif ext in PDF_TYPES:
        _render_pdf(uploaded)

    elif ext in AUDIO_TYPES:
        _render_audio(uploaded)

    elif ext in VIDEO_TYPES:
        _render_video(uploaded)

    elif ext in EXCEL_TYPES:
        _render_excel(uploaded)

    elif ext in DOCX_TYPES:
        _render_docx(uploaded)

    else:
        st.warning(f"⚠️ `.{ext}` is not directly previewable. Downloading instead.")
        st.download_button("⬇️ Download File", uploaded.getvalue(),
                           file_name=uploaded.name, use_container_width=True, key="fv_dl_fallback")

    # ── Footer ─────────────────────────────────────────────────────────────────
    st.markdown("---")
    if st.button("💬 Back to Chat", use_container_width=True, key="fv_back"):
        st.session_state.app_mode = "chat"
        st.rerun()

