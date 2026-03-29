"""
code_converter_engine.py — Enhanced Code Converter with AI
"""

import streamlit as st
import io
import zipfile
import re
from utils import ai_engine

SUPPORTED_LANGUAGES = [
    "Python", "Java", "C++", "C", "C#", "JavaScript", "TypeScript",
    "Go", "Rust", "Ruby", "PHP", "Swift", "Kotlin", "Dart",
    "R", "Scala", "Perl", "Lua", "Haskell", "Elixir",
]

FRAMEWORK_MAP = {
    "Flask": "Express.js", "Django": "Spring Boot", "FastAPI": "Gin (Go)",
    "Express": "FastAPI", "Spring": "Django", "Rails": "Django",
    "React": "Vue.js", "Angular": "React", "Vue": "React",
    "Next.js": "Nuxt.js", "Nuxt": "Next.js",
}

LANG_EXTENSIONS = {
    "Python": ".py", "Java": ".java", "C++": ".cpp", "C": ".c",
    "C#": ".cs", "JavaScript": ".js", "TypeScript": ".ts",
    "Go": ".go", "Rust": ".rs", "Ruby": ".rb", "PHP": ".php",
    "Swift": ".swift", "Kotlin": ".kt", "Dart": ".dart",
    "R": ".r", "Scala": ".scala", "Perl": ".pl", "Lua": ".lua",
    "Haskell": ".hs", "Elixir": ".ex",
}


def convert_code(code: str, source_lang: str, target_lang: str, explain: bool = False) -> dict:
    prompt = f"""Convert this {source_lang} code to {target_lang}. 
Return ONLY a JSON object with these keys:
- "converted": the converted code as a string
- "token_count": estimated tokens used (integer)
{"- \"explanation\": for each significant change, explain WHY the idiom differs (as a list of strings)" if explain else ""}

Source code:
```{source_lang.lower()}
{code}
```"""

    try:
        result = ai_engine.generate(
            prompt=prompt,
            model="llama-4-scout-17b-16e-instruct",
            json_mode=True,
            max_tokens=8192,
            temperature=0.2,
        )
        import json
        try:
            data = json.loads(result)
        except json.JSONDecodeError:
            code_match = re.search(r'```\w*\n(.*?)```', result, re.DOTALL)
            data = {
                "converted": code_match.group(1) if code_match else result,
                "token_count": len(result.split()) * 2,
            }
            if explain:
                data["explanation"] = ["Conversion completed — see converted code above."]
        return data
    except Exception as e:
        return {"converted": "", "token_count": 0, "error": str(e)}


def execution_preview(code: str, language: str) -> str:
    prompt = f"""Perform a dry-run of this {language} code. Show the expected console output line by line.
If the code has errors, show what error would occur. Be precise.
Return ONLY the expected output, nothing else.

```{language.lower()}
{code}
```"""
    try:
        return ai_engine.generate(prompt=prompt, model="llama-3.1-8b-instant", max_tokens=2048, temperature=0.1)
    except Exception as e:
        return f"Preview unavailable: {e}"


def detect_framework(code: str) -> str:
    indicators = {
        "Flask": ["from flask", "Flask(__name__)", "@app.route"],
        "Django": ["from django", "django.conf", "urlpatterns"],
        "FastAPI": ["from fastapi", "FastAPI()", "@app.get"],
        "Express": ["require('express')", "express()", "app.get("],
        "Spring": ["@SpringBootApplication", "@RestController", "SpringApplication.run"],
        "Rails": ["class ApplicationController", "Rails.application"],
        "React": ["import React", "useState", "useEffect"],
        "Angular": ["@Component", "@NgModule", "angular/core"],
        "Vue": ["createApp", "defineComponent", "ref("],
    }
    code_lower = code.lower()
    for framework, patterns in indicators.items():
        for pattern in patterns:
            if pattern.lower() in code_lower:
                return framework
    return ""


def batch_chain_convert(code: str, source_lang: str, chain: list) -> list:
    results = []
    current_code = code
    current_lang = source_lang
    for target_lang in chain:
        if target_lang == current_lang:
            continue
        result = convert_code(current_code, current_lang, target_lang)
        converted = result.get("converted", "")
        results.append({
            "from": current_lang,
            "to": target_lang,
            "code": converted,
            "tokens": result.get("token_count", 0),
        })
        if converted:
            current_code = converted
            current_lang = target_lang
        else:
            break
    return results


def convert_zip(zip_bytes: bytes, source_lang: str, target_lang: str) -> bytes:
    output_buffer = io.BytesIO()
    src_ext = LANG_EXTENSIONS.get(source_lang, "")
    tgt_ext = LANG_EXTENSIONS.get(target_lang, "")

    with zipfile.ZipFile(io.BytesIO(zip_bytes), 'r') as zin:
        with zipfile.ZipFile(output_buffer, 'w', zipfile.ZIP_DEFLATED) as zout:
            for file_info in zin.infolist():
                if file_info.is_dir():
                    continue
                content = zin.read(file_info.filename).decode('utf-8', errors='replace')
                if src_ext and file_info.filename.endswith(src_ext):
                    result = convert_code(content, source_lang, target_lang)
                    converted = result.get("converted", content)
                    new_name = file_info.filename.rsplit('.', 1)[0] + tgt_ext
                    zout.writestr(new_name, converted)
                else:
                    zout.writestr(file_info.filename, content)

    output_buffer.seek(0)
    return output_buffer.read()


def chat_about_code(question: str, original_code: str, converted_code: str, source_lang: str, target_lang: str) -> str:
    prompt = f"""Context: Code was converted from {source_lang} to {target_lang}.

Original ({source_lang}):
```
{original_code[:1500]}
```

Converted ({target_lang}):
```
{converted_code[:1500]}
```

User question: {question}

Answer concisely, referencing specific lines when relevant."""

    try:
        return ai_engine.generate(prompt=prompt, model="llama-4-scout-17b-16e-instruct", max_tokens=2048, temperature=0.4)
    except Exception as e:
        return f"Chat unavailable: {e}"


def generate_diff_html(original: str, converted: str, source_lang: str, target_lang: str) -> str:
    orig_lines = original.split('\n')
    conv_lines = converted.split('\n')
    max_lines = max(len(orig_lines), len(conv_lines))

    rows = ""
    for i in range(max_lines):
        left = orig_lines[i] if i < len(orig_lines) else ""
        right = conv_lines[i] if i < len(conv_lines) else ""
        left_esc = left.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        right_esc = right.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        rows += f"""<tr>
<td style="padding:2px 8px;color:#888;text-align:right;user-select:none;border-right:1px solid #333;width:30px;">{i+1}</td>
<td style="padding:2px 8px;font-family:monospace;font-size:.82rem;white-space:pre-wrap;background:rgba(248,113,113,0.04);">{left_esc}</td>
<td style="padding:2px 8px;color:#888;text-align:right;user-select:none;border-right:1px solid #333;border-left:2px solid #555;width:30px;">{i+1}</td>
<td style="padding:2px 8px;font-family:monospace;font-size:.82rem;white-space:pre-wrap;background:rgba(52,211,153,0.04);">{right_esc}</td>
</tr>"""

    return f"""<div style="overflow-x:auto;border:1px solid var(--bd-glass);border-radius:12px;margin:12px 0;">
<table style="width:100%;border-collapse:collapse;">
<thead><tr>
<th colspan="2" style="padding:8px;background:rgba(248,113,113,0.1);color:#f87171;font-size:.8rem;text-align:center;">{source_lang} (Original)</th>
<th colspan="2" style="padding:8px;background:rgba(52,211,153,0.1);color:#34d399;font-size:.8rem;text-align:center;">{target_lang} (Converted)</th>
</tr></thead>
<tbody>{rows}</tbody>
</table></div>"""


def render_code_converter():
    st.markdown("""
<style>
.cc-header{background:linear-gradient(135deg,#0a0a2e 0%,#050520 100%);border:1px solid #3d2a6b;border-radius:16px;padding:28px 32px;margin-bottom:20px;}
.cc-title{font-size:2rem;font-weight:900;background:linear-gradient(135deg,#a78bfa,#60a5fa);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin:0 0 4px;}
.cc-sub{font-size:.9rem;color:#9090b8;}
</style>
""", unsafe_allow_html=True)

    st.markdown("""
<div class="cc-header">
  <div class="cc-title">🔄 Enhanced Code Converter</div>
  <div class="cc-sub">AI-powered code translation · Side-by-side diff · Multi-file zip · Framework-aware · Batch chain</div>
</div>
""", unsafe_allow_html=True)

    if "cc_converted" not in st.session_state:
        st.session_state.cc_converted = ""
    if "cc_original" not in st.session_state:
        st.session_state.cc_original = ""
    if "cc_tokens" not in st.session_state:
        st.session_state.cc_tokens = 0
    if "cc_chat_messages" not in st.session_state:
        st.session_state.cc_chat_messages = []

    tab_single, tab_zip, tab_chain, tab_chat = st.tabs([
        "🔄 Single Convert", "📦 Multi-File (ZIP)", "⛓️ Batch Chain", "💬 Code Chat"
    ])

    with tab_single:
        c1, c2 = st.columns(2)
        with c1:
            source_lang = st.selectbox("From", SUPPORTED_LANGUAGES, index=0, key="cc_from")
        with c2:
            target_lang = st.selectbox("To", SUPPORTED_LANGUAGES, index=1, key="cc_to")

        code_input = st.text_area("Paste your code", height=250, key="cc_code",
                                  placeholder="Paste your source code here...")
        st.session_state.cc_original = code_input

        fw = detect_framework(code_input) if code_input else ""
        if fw:
            target_fw = FRAMEWORK_MAP.get(fw, "equivalent framework")
            st.info(f"🔍 Detected **{fw}** framework — will convert to **{target_fw}** equivalent")

        show_explain = st.checkbox("Show conversion explanation (why each change was made)", key="cc_explain")
        show_preview = st.checkbox("Show execution preview (dry-run)", key="cc_preview")
        show_diff = st.checkbox("Show side-by-side diff view", value=True, key="cc_diff")

        b1, b2 = st.columns([3, 1])
        with b1:
            convert_btn = st.button("🚀 Convert Code", type="primary", use_container_width=True,
                                    disabled=not code_input.strip(), key="cc_convert")
        with b2:
            if st.button("💬 Back", use_container_width=True, key="cc_back"):
                st.session_state.app_mode = "chat"
                st.rerun()

        if convert_btn and code_input.strip():
            with st.spinner(f"Converting {source_lang} → {target_lang}..."):
                result = convert_code(code_input, source_lang, target_lang, explain=show_explain)

            if result.get("error"):
                st.error(f"Conversion failed: {result['error']}")
            else:
                converted = result.get("converted", "")
                tokens = result.get("token_count", 0)
                st.session_state.cc_converted = converted
                st.session_state.cc_tokens = tokens
                st.session_state.total_tokens_used = st.session_state.get("total_tokens_used", 0) + tokens

                if show_diff and converted:
                    st.markdown(generate_diff_html(code_input, converted, source_lang, target_lang),
                                unsafe_allow_html=True)
                else:
                    st.code(converted, language=target_lang.lower())

                st.caption(f"🔢 Tokens used: {tokens}")

                if show_explain and result.get("explanation"):
                    with st.expander("📖 Conversion Explanation"):
                        for exp in result["explanation"]:
                            st.markdown(f"• {exp}")

                if show_preview and converted:
                    with st.expander("▶️ Execution Preview (AI Dry-Run)"):
                        with st.spinner("Simulating execution..."):
                            preview = execution_preview(converted, target_lang)
                        st.code(preview, language="text")

                ext = LANG_EXTENSIONS.get(target_lang, ".txt")
                st.download_button(
                    f"📥 Download {ext}",
                    converted,
                    file_name=f"converted{ext}",
                    mime="text/plain",
                    use_container_width=True,
                    key="cc_dl",
                )

    with tab_zip:
        st.markdown("### 📦 Multi-File Conversion")
        st.caption("Upload a .zip of source files — all matching files will be converted and re-zipped.")
        zc1, zc2 = st.columns(2)
        with zc1:
            zip_source = st.selectbox("Source language", SUPPORTED_LANGUAGES, key="cc_zip_from")
        with zc2:
            zip_target = st.selectbox("Target language", SUPPORTED_LANGUAGES, index=1, key="cc_zip_to")

        zip_file = st.file_uploader("Upload ZIP file", type=["zip"], key="cc_zip_upload")

        if zip_file and st.button("🔄 Convert All Files", type="primary", use_container_width=True, key="cc_zip_btn"):
            with st.spinner("Converting all files in ZIP..."):
                try:
                    result_bytes = convert_zip(zip_file.read(), zip_source, zip_target)
                    st.success("✅ All files converted!")
                    st.download_button(
                        "📥 Download Converted ZIP",
                        result_bytes,
                        file_name=f"converted_{zip_target.lower()}.zip",
                        mime="application/zip",
                        use_container_width=True,
                        key="cc_zip_dl",
                    )
                except Exception as e:
                    st.error(f"ZIP conversion failed: {e}")

    with tab_chain:
        st.markdown("### ⛓️ Batch Language Chain")
        st.caption("Convert through multiple languages in sequence: Python → Java → C++ in one click.")

        chain_code = st.text_area("Source code", height=200, key="cc_chain_code",
                                  placeholder="Paste source code...")
        chain_source = st.selectbox("Starting language", SUPPORTED_LANGUAGES, key="cc_chain_from")
        chain_targets = st.multiselect("Chain through (in order)",
                                       [l for l in SUPPORTED_LANGUAGES if l != chain_source],
                                       default=["Java", "C++"] if chain_source == "Python" else [],
                                       key="cc_chain_targets")

        if chain_code.strip() and chain_targets:
            if st.button("⛓️ Run Chain Conversion", type="primary", use_container_width=True, key="cc_chain_btn"):
                with st.spinner("Running conversion chain..."):
                    results = batch_chain_convert(chain_code, chain_source, chain_targets)

                for i, step in enumerate(results):
                    with st.expander(f"Step {i+1}: {step['from']} → {step['to']} ({step['tokens']} tokens)", expanded=True):
                        ext = LANG_EXTENSIONS.get(step['to'], '')
                        st.code(step['code'], language=step['to'].lower())
                        st.download_button(
                            f"📥 Download {ext}",
                            step['code'],
                            file_name=f"chain_step_{i+1}{ext}",
                            mime="text/plain",
                            key=f"cc_chain_dl_{i}",
                        )

    with tab_chat:
        st.markdown("### 💬 Ask About Your Conversion")
        st.caption("Ask questions about the converted code — AI answers in context.")

        if st.session_state.cc_converted:
            for msg in st.session_state.cc_chat_messages:
                role_icon = "🧑" if msg["role"] == "user" else "🤖"
                bg = "rgba(124,106,247,0.08)" if msg["role"] == "user" else "rgba(52,211,153,0.06)"
                st.markdown(f'<div style="background:{bg};border-radius:10px;padding:10px 14px;margin:6px 0;font-size:.9rem;">{role_icon} {msg["content"]}</div>',
                            unsafe_allow_html=True)

            chat_q = st.text_input("Ask about the conversion", placeholder='e.g. "Why ArrayList instead of array?"',
                                   key="cc_chat_q")
            if st.button("📤 Ask", type="primary", use_container_width=True, key="cc_chat_send") and chat_q.strip():
                st.session_state.cc_chat_messages.append({"role": "user", "content": chat_q})
                with st.spinner("Thinking..."):
                    answer = chat_about_code(
                        chat_q, st.session_state.cc_original,
                        st.session_state.cc_converted,
                        st.session_state.get("cc_from", "Python"),
                        st.session_state.get("cc_to", "Java"),
                    )
                    st.session_state.cc_chat_messages.append({"role": "assistant", "content": answer})
                st.rerun()

            if st.button("🗑️ Clear Chat", key="cc_chat_clear"):
                st.session_state.cc_chat_messages = []
                st.rerun()
        else:
            st.info("Convert some code first, then come here to ask questions about it.")
