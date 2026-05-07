"""smart_reader_addon.py — Bulk PDF batch + OCR table extraction + smart search + Media Hub"""
import streamlit as st, io, zipfile

def render_smart_reader_addon():
    sa1, sa2, sa3, sa4, sa5, sa6, sa7 = st.tabs([
        "📦 Bulk PDF Batch",
        "📊 OCR Table Extractor",
        "🔎 Smart Document Search",
        "🖼️ Image Explorer",
        "🤖 Mini AI Answerer",
        "🔥 AI & OSS Trends",
        "📚 E-Book & Audio",
    ])

    with sa1:
        st.markdown("**📦 Bulk PDF Batch Processor**")
        st.markdown("""
        <div style="background:rgba(99,102,241,0.07);border:1px solid rgba(99,102,241,0.2);
            border-radius:12px;padding:12px 16px;margin-bottom:16px;font-size:0.85rem;color:rgba(255,255,255,0.6);">
        📤 Upload multiple PDFs — AI will process all of them and give you a combined ZIP of results.
        </div>""", unsafe_allow_html=True)
        pdfs = st.file_uploader("Upload PDFs (multiple):", type=["pdf"], accept_multiple_files=True, key="sra_pdfs")
        batch_action = st.selectbox("Action for ALL PDFs:", [
            "Extract all text","Summarize each PDF","Generate key points from each",
            "Create quiz from each","Extract all headings"
        ], key="sra_batch_action")
        if pdfs and st.button("🚀 Process All PDFs", type="primary", use_container_width=True, key="sra_batch_btn"):
            try:
                import fitz
            except ImportError:
                st.error("PyMuPDF required: pip install pymupdf"); st.stop()
            results = {}
            prog = st.progress(0, f"Processing 0/{len(pdfs)}")
            for i, pdf_file in enumerate(pdfs):
                prog.progress(int(i/len(pdfs)*90), f"Processing {pdf_file.name}...")
                try:
                    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
                    text = "\n".join(page.get_text() for page in doc)[:6000]
                    if batch_action == "Extract all text":
                        results[pdf_file.name] = text
                    else:
                        from utils.ai_engine import generate
                        prompts = {
                            "Summarize each PDF": f"Summarize this document in 5 bullet points:\n{text}",
                            "Generate key points from each": f"List 10 key points from this document:\n{text}",
                            "Create quiz from each": f"Create 5 MCQ quiz questions from this document:\n{text}",
                            "Extract all headings": f"List all headings and section titles from this document:\n{text}",
                        }
                        results[pdf_file.name] = generate(prompts[batch_action], max_tokens=1000)
                except Exception as e:
                    results[pdf_file.name] = f"Error: {e}"
            prog.progress(100, "Done!")
            # Create ZIP
            zip_buf = io.BytesIO()
            with zipfile.ZipFile(zip_buf, "w") as zf:
                for fname, content in results.items():
                    zf.writestr(fname.replace(".pdf","_result.txt"), content)
            zip_buf.seek(0)
            st.success(f"✅ Processed {len(pdfs)} PDFs!")
            st.download_button("⬇️ Download All Results (ZIP)", zip_buf.getvalue(), "batch_results.zip", key="sra_batch_dl")
            # Preview
            for fname, content in list(results.items())[:3]:
                with st.expander(f"Preview: {fname}"):
                    st.text(content[:500])

    with sa2:
        st.markdown("**📊 OCR Table Extractor**")
        img_file = st.file_uploader("Upload image with table/text:", type=["png","jpg","jpeg","webp"], key="sra_ocr_img")
        if img_file:
            st.image(img_file, use_container_width=True)
            extract_type = st.selectbox("Extract as:", ["Structured Text","CSV/Table","JSON","Markdown Table"], key="sra_ocr_type")
            if st.button("📊 Extract with AI OCR", type="primary", use_container_width=True, key="sra_ocr_btn"):
                import base64
                img_bytes = img_file.read()
                b64 = base64.b64encode(img_bytes).decode()
                mime = f"image/{img_file.type.split('/')[-1]}"
                prompts = {
                    "Structured Text": "Extract all text from this image. Preserve formatting and structure.",
                    "CSV/Table": "Extract the table from this image as CSV format with proper headers.",
                    "JSON": "Extract all data from this image as a structured JSON object.",
                    "Markdown Table": "Extract the table from this image in Markdown table format.",
                }
                with st.spinner("Extracting..."):
                    try:
                        from utils.ai_engine import vision_generate
                        result = vision_generate(prompt=prompts[extract_type], image_b64=b64, mime=mime, max_tokens=2000)
                        st.code(result, language="csv" if "CSV" in extract_type else "json" if "JSON" in extract_type else None)
                        st.download_button("📥 Download", result, f"extracted.{'csv' if 'CSV' in extract_type else 'json' if 'JSON' in extract_type else 'txt'}", key="sra_ocr_dl")
                    except Exception as e:
                        st.error(f"Vision AI error: {e}")

    with sa3:
        st.markdown("**🔎 Smart Document Search**")
        doc_text = st.text_area("Paste document text:", height=150, key="sra_search_doc", placeholder="Paste your document content here...")
        search_q = st.text_input("What do you want to find?", placeholder="e.g. mentions of climate change, all dates, phone numbers", key="sra_search_q")
        search_mode = st.selectbox("Search mode:", ["Semantic (AI)","Find exact phrases","Extract all numbers","Extract all dates","Find named entities"], key="sra_search_mode")
        if doc_text and search_q and st.button("🔎 Search", type="primary", use_container_width=True, key="sra_search_btn"):
            if search_mode == "Semantic (AI)":
                with st.spinner("Searching semantically..."):
                    try:
                        from utils.ai_engine import generate
                        ans = generate(f"In this document, find and quote all relevant passages about '{search_q}'. Include line context.\n\nDocument:\n{doc_text[:5000]}")
                        st.markdown(ans)
                    except Exception as e: st.error(str(e))
            elif search_mode == "Extract all numbers":
                import re
                nums = re.findall(r'\b\d+\.?\d*\b', doc_text)
                st.write(f"Found {len(nums)} numbers:", nums[:50])
            elif search_mode == "Extract all dates":
                import re
                dates = re.findall(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}\b|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{1,2},?\s+\d{4}\b', doc_text, re.I)
                st.write(f"Found {len(dates)} dates:", dates)
            elif search_mode == "Find exact phrases":
                if search_q.lower() in doc_text.lower():
                    idx = doc_text.lower().find(search_q.lower())
                    st.success(f"Found at position {idx}:")
                    st.markdown(f"`...{doc_text[max(0,idx-100):idx+200]}...`")
                else:
                    st.warning("Phrase not found.")
            else:
                with st.spinner("Extracting entities..."):
                    try:
                        from utils.ai_engine import generate
                        ans = generate(f"Extract all named entities (people, places, organizations, dates, quantities) from this text:\n{doc_text[:4000]}")
                        st.markdown(ans)
                    except Exception as e: st.error(str(e))

    # ── New tabs: delegate to media_hub_addon ──────────────────────────────────
    with sa4:
        try:
            from media_hub_addon import _tab_image_explorer
            _tab_image_explorer()
        except Exception as e:
            st.error(f"Image Explorer error: {e}")

    with sa5:
        try:
            from media_hub_addon import _tab_mini_ai
            _tab_mini_ai()
        except Exception as e:
            st.error(f"Mini AI Answerer error: {e}")

    with sa6:
        try:
            from media_hub_addon import _tab_trends
            _tab_trends()
        except Exception as e:
            st.error(f"AI & OSS Trends error: {e}")

    with sa7:
        try:
            from media_hub_addon import _tab_ebook
            _tab_ebook()
        except Exception as e:
            st.error(f"E-Book & Audio error: {e}")
