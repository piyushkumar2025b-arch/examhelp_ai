"""sources_addon.py — Step 28: Source credibility scorer + citation exporter"""
import streamlit as st

TRUSTED_DOMAINS = {
    "nature.com":95,"science.org":95,"pubmed.ncbi.nlm.nih.gov":94,"arxiv.org":88,
    "wikipedia.org":72,"bbc.com":85,"reuters.com":88,"who.int":92,"gov":90,
    "edu":85,"nytimes.com":80,"theguardian.com":78,"medium.com":45,"reddit.com":30,
    "quora.com":35,"blogspot.com":25,"wordpress.com":25,
}

def _score_url(url: str) -> tuple:
    url = url.lower().strip()
    for domain, score in TRUSTED_DOMAINS.items():
        if domain in url:
            if score >= 85: return score, "✅ Highly Credible", "#10b981"
            if score >= 65: return score, "⚠️ Generally Reliable", "#f59e0b"
            return score, "❌ Low Credibility", "#ef4444"
    return 50, "❓ Unknown Source", "#818cf8"

def render_sources_addon():
    sa1, sa2, sa3 = st.tabs(["🔍 Credibility Checker", "📜 Citation Exporter", "📚 Trusted Sources"])

    with sa1:
        st.markdown("**🔍 Source Credibility Scorer**")
        urls_input = st.text_area("Enter URLs (one per line):",
                                   placeholder="https://nature.com/article/...\nhttps://medium.com/...",
                                   height=120, key="sa_urls")
        if urls_input and st.button("🔍 Check Credibility", type="primary", use_container_width=True, key="sa_check"):
            urls = [u.strip() for u in urls_input.split("\n") if u.strip()]
            for url in urls:
                score, label, color = _score_url(url)
                bar_w = score
                st.markdown(f"""
                <div style="background:rgba(10,14,30,0.85);border:1px solid rgba(255,255,255,0.07);
                    border-radius:13px;padding:14px 18px;margin-bottom:10px;">
                    <div style="font-size:0.78rem;color:rgba(255,255,255,0.4);margin-bottom:6px;word-break:break-all;">{url[:80]}</div>
                    <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">
                        <div style="font-weight:700;font-size:1.1rem;color:{color};">{score}/100</div>
                        <div style="font-size:0.85rem;color:{color};">{label}</div>
                    </div>
                    <div style="background:rgba(255,255,255,0.06);border-radius:100px;height:6px;">
                        <div style="background:{color};width:{bar_w}%;height:100%;border-radius:100px;"></div>
                    </div>
                </div>""", unsafe_allow_html=True)
            # AI deep analysis
            if st.button("🤖 AI Detailed Analysis", key="sa_ai_check"):
                with st.spinner("Analyzing..."):
                    try:
                        from utils.ai_engine import generate
                        ans = generate(f"Evaluate the credibility and bias of these sources: {urls_input[:500]}. For each: reputation, potential bias, fact-checking record, and recommendation.")
                        st.markdown(ans)
                    except Exception as e: st.error(str(e))

    with sa2:
        st.markdown("**📜 Bulk Citation Exporter**")
        cite_urls = st.text_area("Paste URLs to cite (one per line):", height=100, key="sa_cite_urls")
        cite_fmt = st.selectbox("Format:", ["APA 7th","MLA 9th","Chicago","IEEE"], key="sa_cite_fmt2")
        if cite_urls and st.button("📜 Generate Citations", type="primary", use_container_width=True, key="sa_cite_gen"):
            with st.spinner("Generating..."):
                try:
                    from utils.ai_engine import generate
                    ans = generate(f"Generate {cite_fmt} citations for these URLs: {cite_urls[:1000]}. Output only formatted citations, numbered.")
                    st.markdown(ans)
                    st.download_button("📥 Download Citations", ans, "citations.txt", key="sa_cite_dl")
                except Exception as e: st.error(str(e))

    with sa3:
        st.markdown("**📚 Trusted Academic & News Sources**")
        categories = {
            "🔬 Science & Research": ["nature.com","science.org","pubmed.ncbi.nlm.nih.gov","arxiv.org","jstor.org"],
            "📰 News": ["reuters.com","bbc.com","apnews.com","theguardian.com","nytimes.com"],
            "🏛️ Government / Official": ["who.int","cdc.gov","nasa.gov","un.org","data.gov"],
            "📖 Reference": ["britannica.com","wikipedia.org","wolframalpha.com"],
            "💻 Tech": ["stackoverflow.com","github.com","developer.mozilla.org","docs.python.org"],
        }
        for cat, sources in categories.items():
            st.markdown(f"**{cat}**")
            st.markdown(" · ".join(f"`{s}`" for s in sources))
            st.markdown("")
