"""
research_addon.py — Steps 11-12
Additions: Multi-source search (arXiv + Wikipedia + OpenAlex), Citation generator,
Research outline builder, Literature review AI, Mind map generator
"""
import streamlit as st
import urllib.request, urllib.parse, json, io

def _search_arxiv(query: str, max_results: int = 5) -> list:
    try:
        q = urllib.parse.quote(query)
        url = f"http://export.arxiv.org/api/query?search_query=all:{q}&start=0&max_results={max_results}"
        req = urllib.request.Request(url, headers={"User-Agent":"ExamHelp/1.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            raw = r.read().decode()
        import re
        titles = re.findall(r'<title>(.*?)</title>', raw, re.DOTALL)[1:]
        summaries = re.findall(r'<summary>(.*?)</summary>', raw, re.DOTALL)
        ids = re.findall(r'<id>(.*?)</id>', raw)
        results = []
        for i in range(min(len(titles), max_results)):
            results.append({
                "title": titles[i].strip().replace('\n',' '),
                "summary": summaries[i].strip()[:300] if i < len(summaries) else "",
                "url": ids[i+1].strip() if i+1 < len(ids) else "https://arxiv.org"
            })
        return results
    except Exception as e:
        return [{"error": str(e)}]

def _search_wikipedia(query: str) -> dict:
    try:
        q = urllib.parse.quote(query)
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{q}"
        req = urllib.request.Request(url, headers={"User-Agent":"ExamHelp/1.0"})
        with urllib.request.urlopen(req, timeout=6) as r:
            data = json.loads(r.read().decode())
        return {"title": data.get("title",""), "extract": data.get("extract",""),
                "url": data.get("content_urls",{}).get("desktop",{}).get("page","")}
    except Exception:
        return {}

def render_research_addon():
    st.markdown("""
    <style>
    .ra-paper { background:rgba(10,14,30,0.8);border:1px solid rgba(99,102,241,0.15);
        border-radius:14px;padding:16px 18px;margin-bottom:12px;
        transition:all 0.25s ease; }
    .ra-paper:hover { border-color:rgba(99,102,241,0.4);transform:translateX(4px); }
    .ra-title { font-weight:700;color:rgba(255,255,255,0.9);font-size:0.95rem;margin-bottom:6px; }
    .ra-abs { font-size:0.82rem;color:rgba(255,255,255,0.5);line-height:1.6; }
    .ra-src-tag { display:inline-block;background:rgba(99,102,241,0.1);
        border:1px solid rgba(99,102,241,0.2);border-radius:100px;
        padding:2px 10px;font-size:0.65rem;color:#818cf8;margin-right:8px;
        font-family:'JetBrains Mono',monospace;letter-spacing:1px; }
    </style>""", unsafe_allow_html=True)

    r1,r2,r3,r4,r5 = st.tabs([
        "🔍 Multi-Source Search","📜 Citation Generator","🗺️ Research Outline",
        "📖 Literature Review","🧠 Mind Map"
    ])

    with r1:
        query = st.text_input("Research query:", placeholder="e.g. quantum computing machine learning",
                               key="ra_query")
        sources = st.multiselect("Sources:", ["arXiv (Scientific Papers)","Wikipedia","AI Knowledge Base"],
                                  default=["arXiv (Scientific Papers)","Wikipedia"], key="ra_sources")
        max_r = st.slider("Max results per source:", 2, 10, 5, key="ra_max")

        if query and st.button("🔍 Search All Sources", type="primary", use_container_width=True, key="ra_search"):
            all_results = []

            if "arXiv (Scientific Papers)" in sources:
                with st.spinner("Searching arXiv..."):
                    papers = _search_arxiv(query, max_r)
                    for p in papers:
                        if "error" not in p:
                            st.markdown(f"""
                            <div class="ra-paper">
                                <span class="ra-src-tag">arXiv</span>
                                <div class="ra-title">{p['title']}</div>
                                <div class="ra-abs">{p['summary']}...</div>
                                <a href="{p['url']}" target="_blank" style="color:#818cf8;font-size:0.78rem;">Read Paper →</a>
                            </div>""", unsafe_allow_html=True)

            if "Wikipedia" in sources:
                with st.spinner("Searching Wikipedia..."):
                    wiki = _search_wikipedia(query)
                    if wiki.get("title"):
                        st.markdown(f"""
                        <div class="ra-paper">
                            <span class="ra-src-tag">Wikipedia</span>
                            <div class="ra-title">{wiki['title']}</div>
                            <div class="ra-abs">{wiki['extract'][:400]}</div>
                            <a href="{wiki['url']}" target="_blank" style="color:#818cf8;font-size:0.78rem;">Read Article →</a>
                        </div>""", unsafe_allow_html=True)

            if "AI Knowledge Base" in sources:
                with st.spinner("Querying AI knowledge base..."):
                    try:
                        from utils.ai_engine import generate
                        ai_r = generate(f"Provide a comprehensive research summary on '{query}': key findings, leading researchers, recent developments, controversies, and future directions. Include 5 key references.", max_tokens=2000)
                        st.markdown(f"""
                        <div class="ra-paper">
                            <span class="ra-src-tag">AI Knowledge</span>
                            <div style="font-size:0.9rem;color:rgba(255,255,255,0.75);line-height:1.8;">{ai_r}</div>
                        </div>""", unsafe_allow_html=True)
                    except Exception as e: st.error(str(e))

    with r2:
        cite_title = st.text_input("Paper/Book Title:", key="ra_cite_title")
        cite_author = st.text_input("Author(s):", placeholder="Smith, J., & Jones, A.", key="ra_cite_author")
        cite_year = st.number_input("Year:", value=2024, min_value=1800, max_value=2030, key="ra_cite_year")
        cite_journal = st.text_input("Journal/Publisher:", key="ra_cite_journal")
        cite_url = st.text_input("URL (optional):", key="ra_cite_url")
        cite_format = st.selectbox("Format:", ["APA 7th","MLA 9th","Chicago","Harvard","IEEE"], key="ra_cite_fmt")

        if cite_title and st.button("📜 Generate Citation", type="primary", use_container_width=True, key="ra_cite_btn"):
            try:
                from utils.ai_engine import generate
                cite_p = f"Generate a {cite_format} citation for: Title: {cite_title}, Author(s): {cite_author}, Year: {cite_year}, Journal/Publisher: {cite_journal}, URL: {cite_url}. Output only the formatted citation."
                cit = generate(cite_p, max_tokens=300, temperature=0.1)
                st.markdown(f"""
                <div style="background:rgba(10,14,30,0.85);border:1px solid rgba(99,102,241,0.25);
                    border-radius:14px;padding:18px;font-family:'JetBrains Mono',monospace;
                    font-size:0.85rem;color:#c7d2fe;line-height:1.7;">{cit}</div>""", unsafe_allow_html=True)
                st.download_button("📥 Save Citation", cit, "citation.txt", key="ra_cite_dl")
            except Exception as e: st.error(str(e))

    with r3:
        outline_topic = st.text_input("Research Topic:", placeholder="e.g. Impact of AI on healthcare", key="ra_outline_topic")
        outline_type = st.selectbox("Document Type:", ["Research Paper","Thesis","Literature Review","Report","Dissertation"], key="ra_outline_type")
        outline_len = st.selectbox("Length:", ["Short (4-5 sections)","Medium (6-8 sections)","Long (10+ sections)"], key="ra_outline_len")
        if outline_topic and st.button("🗺️ Generate Research Outline", type="primary", use_container_width=True, key="ra_outline_btn"):
            with st.spinner("Building research outline..."):
                try:
                    from utils.ai_engine import generate
                    p = f"Create a detailed {outline_type} outline for topic: '{outline_topic}'. Length: {outline_len}. Include: main sections, sub-sections, what to cover in each, estimated word count, and suggested sources to look for."
                    outline = generate(p, max_tokens=2500, temperature=0.3)
                    st.markdown(outline)
                    st.download_button("📥 Save Outline", outline, "research_outline.txt", key="ra_outline_dl")
                except Exception as e: st.error(str(e))

    with r4:
        lit_topic = st.text_input("Topic for Literature Review:", key="ra_lit_topic")
        lit_period = st.text_input("Time period:", value="2015-2024", key="ra_lit_period")
        if lit_topic and st.button("📖 Generate Literature Review", type="primary", use_container_width=True, key="ra_lit_btn"):
            with st.spinner("Synthesizing literature..."):
                try:
                    from utils.ai_engine import generate
                    p = f"Write a literature review on '{lit_topic}' covering {lit_period}. Include: thematic synthesis, key authors/works, research gaps, methodological trends, agreements/controversies, and future directions. Write academically with proper citations format."
                    review = generate(p, max_tokens=4000, temperature=0.3)
                    st.markdown(review)
                    st.download_button("📥 Download Review", review, "lit_review.txt", key="ra_lit_dl")
                except Exception as e: st.error(str(e))

    with r5:
        mm_topic = st.text_input("Mind map topic:", placeholder="e.g. Machine Learning", key="ra_mm_topic")
        if mm_topic and st.button("🧠 Generate Mind Map (Text)", type="primary", use_container_width=True, key="ra_mm_btn"):
            with st.spinner("Creating mind map..."):
                try:
                    from utils.ai_engine import generate
                    p = f"Create a detailed mind map for '{mm_topic}' in tree format using indentation. Show: central topic → main branches (5-7) → sub-branches (3-4 each) → leaf nodes (2-3 each). Use → and indentation to show hierarchy."
                    mm = generate(p, max_tokens=2000, temperature=0.4)
                    st.code(mm, language=None)
                    st.download_button("📥 Save Mind Map", mm, "mind_map.txt", key="ra_mm_dl")
                except Exception as e: st.error(str(e))
