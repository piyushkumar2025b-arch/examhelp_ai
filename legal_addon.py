"""
legal_addon.py — Steps 9-10
Additions: Contract clause extractor, red-flag detector, Indian law lookup, legal templates
"""
import streamlit as st

INDIAN_LAWS = {
    "IPC Section 420":"Cheating and dishonestly inducing delivery of property. Punishment: up to 7 years imprisonment + fine.",
    "IPC Section 302":"Punishment for murder. Death sentence or imprisonment for life + fine.",
    "IPC Section 376":"Rape — Minimum 10 years rigorous imprisonment, extendable to life.",
    "Article 19":"Freedom of speech, expression, assembly, movement, profession.",
    "Article 21":"Right to life and personal liberty — cannot be deprived except by law.",
    "Article 32":"Right to constitutional remedies — approach Supreme Court for fundamental rights.",
    "RTI Act 2005":"Right to Information — citizens can request info from govt bodies within 30 days.",
    "Consumer Protection Act 2019":"Protects consumer rights, allows complaints within 2 years of cause of action.",
    "IT Act Section 66A":"STRUCK DOWN by SC. Was misused for online speech.",
    "IT Act Section 67":"Publishing obscene content online — 3 years jail + fine.",
    "Motor Vehicles Act":"Drunk driving: Fine ₹10,000 + 6 months jail. No helmet: ₹1,000.",
    "Labour Law — PF":"12% of basic salary contributed by employee + 12% by employer to EPF.",
    "GST 18%":"Most services taxed at 18% GST.",
    "Copyright Act 1957":"Protects original works for author's lifetime + 60 years.",
    "Companies Act 2013":"Governs incorporation, management, dissolution of companies in India.",
}

RED_FLAGS = [
    "unlimited liability","indemnify at sole discretion","irrevocable license",
    "perpetual license","in perpetuity","without limitation","sole discretion",
    "unilateral modification","non-refundable","no warranty","as-is",
    "waive right to sue","binding arbitration only","class action waiver",
    "auto-renewal","termination without cause","immediate termination",
    "assign this agreement","change terms at any time","sole remedy",
]

def render_legal_addon():
    st.markdown("""
    <style>
    .law-card { background:rgba(10,14,30,0.8);border:1px solid rgba(239,68,68,0.15);
        border-left:3px solid #ef4444;border-radius:14px;padding:16px 18px;margin-bottom:10px; }
    .law-flag { background:rgba(239,68,68,0.08);border:1px solid rgba(239,68,68,0.2);
        border-radius:8px;padding:4px 12px;font-size:0.78rem;color:#fca5a5;display:inline-block;margin:3px; }
    .law-clean { background:rgba(16,185,129,0.08);border:1px solid rgba(16,185,129,0.2);
        border-radius:8px;padding:4px 12px;font-size:0.78rem;color:#6ee7b7;display:inline-block;margin:3px; }
    </style>""", unsafe_allow_html=True)

    la1,la2,la3,la4 = st.tabs([
        "🔍 Contract Analyzer","⚠️ Red Flag Detector","🇮🇳 Indian Law Lookup","📋 Legal Templates"
    ])

    with la1:
        contract_text = st.text_area("Paste contract/agreement text:", height=250,
                                      placeholder="Paste any legal document, contract, terms of service...",
                                      key="la_contract")
        analysis_type = st.selectbox("Analyze for:", [
            "Full Contract Review","Key Clauses Summary","Obligations & Rights",
            "Risk Assessment","Plain English Translation","Missing Clauses"
        ], key="la_analysis_type")
        if contract_text and st.button("⚖️ Analyze Contract", type="primary",
                                        use_container_width=True, key="la_analyze"):
            with st.spinner("Analyzing contract..."):
                try:
                    from utils.ai_engine import generate
                    prompts = {
                        "Full Contract Review": f"Provide a complete legal review of this contract. Identify: parties, key obligations, rights, payment terms, termination clauses, dispute resolution, and any unusual clauses. Rate it 1-10 for fairness.\n\n{contract_text[:8000]}",
                        "Key Clauses Summary": f"Extract and summarize all key clauses from this contract in bullet points. Include: payment, duration, termination, liability, warranties, IP rights.\n\n{contract_text[:8000]}",
                        "Obligations & Rights": f"List all obligations (what you MUST do) and rights (what you CAN do) for each party in this contract.\n\n{contract_text[:8000]}",
                        "Risk Assessment": f"Identify ALL risks in this contract for both parties. Rate each risk High/Medium/Low. Suggest protective amendments.\n\n{contract_text[:8000]}",
                        "Plain English Translation": f"Rewrite this contract in simple, plain English that anyone can understand. Keep all key information.\n\n{contract_text[:8000]}",
                        "Missing Clauses": f"What important clauses are MISSING from this contract? List them with recommendations for what each should say.\n\n{contract_text[:8000]}",
                    }
                    ans = generate(prompts[analysis_type], max_tokens=3000, temperature=0.3)
                    st.markdown(f"""
                    <div style="background:rgba(10,14,30,0.85);border:1px solid rgba(239,68,68,0.2);
                        border-radius:18px;padding:24px;font-size:0.9rem;color:rgba(255,255,255,0.8);
                        line-height:1.85;white-space:pre-wrap;">{ans}</div>
                    """, unsafe_allow_html=True)
                    st.download_button("📥 Download Analysis", ans, "contract_analysis.txt", key="la_dl")
                except Exception as e: st.error(str(e))

    with la2:
        flag_text = st.text_area("Paste text to scan for red flags:", height=200,
                                  placeholder="Paste terms of service, contract, policy...",
                                  key="la_flag_text")
        if flag_text and st.button("🚨 Scan for Red Flags", type="primary",
                                    use_container_width=True, key="la_flag_btn"):
            text_lower = flag_text.lower()
            found_flags = [f for f in RED_FLAGS if f in text_lower]
            if found_flags:
                st.error(f"⚠️ Found {len(found_flags)} red flag(s)!")
                flags_html = "".join(f'<span class="law-flag">🚩 {f}</span>' for f in found_flags)
                st.markdown(f'<div>{flags_html}</div>', unsafe_allow_html=True)
                with st.spinner("Getting AI explanation of risks..."):
                    try:
                        from utils.ai_engine import generate
                        risk_explain = generate(f"These red flag clauses were found in a legal document: {', '.join(found_flags)}. Explain the risk of each one in plain language and what the person should do about them.")
                        st.markdown(risk_explain)
                    except Exception: pass
            else:
                st.success("✅ No common red flags detected. But always consult a lawyer!")
            clean_count = max(0, 15 - len(found_flags))
            st.markdown(f'<div style="margin-top:12px;"><span class="law-clean">✅ {clean_count} standard clauses OK</span></div>', unsafe_allow_html=True)

    with la3:
        search = st.text_input("🔍 Search Indian Laws:", placeholder="e.g. murder, RTI, consumer, copyright",
                               key="la_law_search")
        for law_name, law_desc in INDIAN_LAWS.items():
            if not search or search.lower() in law_name.lower() or search.lower() in law_desc.lower():
                st.markdown(f"""
                <div class="law-card">
                    <div style="font-weight:700;color:rgba(255,255,255,0.9);margin-bottom:6px;">{law_name}</div>
                    <div style="font-size:0.85rem;color:rgba(255,255,255,0.6);line-height:1.65;">{law_desc}</div>
                </div>""", unsafe_allow_html=True)

        st.markdown("---")
        custom_q = st.text_input("Ask about any Indian law:", placeholder="What are my rights if arrested?",
                                  key="la_custom_q")
        if custom_q and st.button("⚖️ Ask AI Legal Expert", key="la_ask_ai", use_container_width=True):
            with st.spinner("Consulting legal database..."):
                try:
                    from utils.ai_engine import generate
                    ans = generate(f"As an Indian law expert: {custom_q}. Provide relevant laws, sections, landmark cases, and practical advice. Add disclaimer about consulting a lawyer.")
                    st.markdown(ans)
                except Exception as e: st.error(str(e))

    with la4:
        tmpl = st.selectbox("Choose Template:", [
            "NDA (Non-Disclosure Agreement)","Freelance Contract","Service Agreement",
            "Rental Agreement","Employment Offer Letter","Partnership Agreement","Privacy Policy"
        ], key="la_tmpl")
        context = st.text_area("Customize (party names, terms, etc.):",
                                placeholder="e.g. Party A: Ravi Sharma, Party B: Tech Corp, Duration: 2 years",
                                height=80, key="la_tmpl_ctx")
        if st.button("📋 Generate Template", type="primary", use_container_width=True, key="la_tmpl_btn"):
            with st.spinner("Generating legal template..."):
                try:
                    from utils.ai_engine import generate
                    ans = generate(f"Generate a professional {tmpl} template. Context: {context or 'Use generic placeholder names'}. Make it complete, legally sound, and formatted professionally with all standard clauses.")
                    st.text_area("Generated Template:", ans, height=400, key="la_tmpl_out")
                    st.download_button("📥 Download Template", ans, f"{tmpl.replace(' ','_')}.txt", key="la_tmpl_dl")
                except Exception as e: st.error(str(e))
