"""
image_generator_addon.py — ExamHelp AI Image Generator UI v2.0
Steps 6-10: Model picker · Instant preview · Gallery tab · Share link · Better UX
All engines are 100% free — zero AI quota usage.
"""
import streamlit as st
import random

# ──────────────────────────────────────────────────────────────────────────────
# CSS (Step 6-10 design tokens)
# ──────────────────────────────────────────────────────────────────────────────
_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Inter:wght@400;500;600;700&family=Space+Mono&display=swap');

/* ── Header ── */
.ig-header {
    background: linear-gradient(135deg,#0a0014 0%,#0d001f 40%,#001428 100%);
    border: 1px solid rgba(139,92,246,0.35); border-radius: 24px;
    padding: 32px 40px; margin-bottom: 24px; position: relative; overflow: hidden;
}
.ig-header::before {
    content:''; position:absolute; inset:0;
    background: radial-gradient(ellipse 60% 80% at 80% 20%,rgba(139,92,246,0.15) 0%,transparent 60%),
                radial-gradient(ellipse 40% 60% at 10% 80%,rgba(6,182,212,0.1) 0%,transparent 60%);
}
.ig-title {
    font-family:'Orbitron',monospace; font-size:clamp(20px,3vw,34px); font-weight:900;
    background:linear-gradient(90deg,#fff 0%,#c4b5fd 40%,#67e8f9 80%);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
    position:relative; margin:0 0 6px;
}
.ig-subtitle {
    font-family:'Space Mono',monospace; font-size:10px; letter-spacing:3px;
    color:rgba(196,181,253,0.55); text-transform:uppercase; position:relative;
}
.ig-badge {
    display:inline-flex; align-items:center; gap:6px;
    background:rgba(139,92,246,0.1); border:1px solid rgba(139,92,246,0.3);
    border-radius:100px; padding:4px 14px; margin-bottom:14px;
    font-family:'Space Mono',monospace; font-size:10px; letter-spacing:2px; color:#c4b5fd;
}
.ig-dot { width:6px;height:6px;border-radius:50%;background:#a78bfa;
    animation:igpulse 1.5s ease-in-out infinite; }
@keyframes igpulse{0%,100%{opacity:1;transform:scale(1);}50%{opacity:.4;transform:scale(.8);}}

/* ── Model cards (Step 6) ── */
.model-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(110px,1fr)); gap:8px; margin:10px 0; }
.model-card {
    border:1px solid rgba(255,255,255,0.07); border-radius:12px;
    padding:10px 8px; text-align:center; cursor:pointer;
    transition:all .2s ease; background:rgba(255,255,255,0.03);
}
.model-card:hover { transform:translateY(-3px); border-color:rgba(139,92,246,0.5);
    background:rgba(139,92,246,0.08); }
.model-card.active { border-color:#8b5cf6; background:rgba(139,92,246,0.15);
    box-shadow:0 0 16px rgba(139,92,246,0.25); }
.model-icon { font-size:20px; display:block; margin-bottom:5px; }
.model-name { font-size:10px; font-weight:600; color:rgba(255,255,255,.75); font-family:'Inter',sans-serif; }
.model-speed { font-size:9px; color:rgba(255,255,255,.3); margin-top:2px; font-family:'Space Mono',monospace; }

/* ── Canvas / empty state ── */
.ig-empty {
    background:linear-gradient(135deg,rgba(10,0,20,0.6),rgba(0,20,40,0.6));
    border:1px dashed rgba(139,92,246,0.2); border-radius:20px;
    min-height:340px; display:flex; align-items:center; justify-content:center;
    text-align:center;
}
.ig-empty-icon { font-size:64px; display:block; opacity:.2; margin-bottom:14px; }
.ig-empty-txt { font-family:'Space Mono',monospace; font-size:11px; letter-spacing:2px;
    color:rgba(255,255,255,.18); }

/* ── Stats pills ── */
.ig-stats { display:flex; gap:8px; flex-wrap:wrap; margin:10px 0; }
.ig-stat { background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.07);
    border-radius:100px; padding:4px 12px;
    font-family:'Space Mono',monospace; font-size:9px; color:rgba(255,255,255,.45); }
.ig-stat b { color:#a78bfa; }

/* ── Share box (Step 9) ── */
.share-box {
    background:rgba(6,182,212,0.05); border:1px solid rgba(6,182,212,0.2);
    border-radius:14px; padding:14px 18px; margin-top:14px;
    font-family:'Space Mono',monospace; font-size:10px; color:rgba(103,232,249,0.7);
    word-break:break-all; line-height:1.7;
}

/* ── Gallery (Step 8) ── */
.gal-item {
    border:1px solid rgba(255,255,255,0.07); border-radius:14px; overflow:hidden;
    transition:all .25s ease; position:relative;
}
.gal-item:hover { transform:scale(1.02); border-color:rgba(139,92,246,0.4);
    box-shadow:0 8px 30px rgba(0,0,0,0.5); }
.gal-meta { padding:8px 10px; background:rgba(0,0,0,0.4);
    font-family:'Inter',sans-serif; font-size:10px; color:rgba(255,255,255,.5); }

/* ── Tip box ── */
.ig-tip {
    background:rgba(139,92,246,0.06); border:1px solid rgba(139,92,246,0.18);
    border-radius:11px; padding:9px 14px; font-size:11px;
    color:rgba(196,181,253,0.65); font-family:'Inter',sans-serif; line-height:1.6;
}

/* ── Prompt char count ── */
.char-count { font-family:'Space Mono',monospace; font-size:10px;
    color:rgba(255,255,255,.3); text-align:right; margin-top:3px; }
</style>
"""


def _header():
    st.markdown(_CSS, unsafe_allow_html=True)
    st.markdown("""
    <div class="ig-header">
        <div class="ig-badge"><div class="ig-dot"></div>
        POLLINATIONS.AI · 8 FREE MODELS · ZERO QUOTA</div>
        <div class="ig-title">🎨 AI Image Generator</div>
        <div class="ig-subtitle">Create any image · Instant preview · Gallery · Share</div>
    </div>
    """, unsafe_allow_html=True)


# ── Step 7: Instant URL image display ──────────────────────────────────────
def _show_image(result: dict, key_suffix: str = ""):
    """Show image — bytes if available, URL fallback (instant)."""
    if result.get("image_bytes"):
        st.image(result["image_bytes"], use_container_width=True)
    elif result.get("image_url"):
        # Step 7: embed via URL — displays instantly without downloading
        st.markdown(
            f'<img src="{result["image_url"]}" '
            f'style="width:100%;border-radius:16px;max-height:580px;object-fit:contain;" />',
            unsafe_allow_html=True,
        )

    # Stats
    st.markdown(f"""
    <div class="ig-stats">
        <div class="ig-stat">Engine <b>{result.get('engine','—')}</b></div>
        <div class="ig-stat">Size <b>{result.get('width')}×{result.get('height')}</b></div>
        <div class="ig-stat">Seed <b>{result.get('seed','—')}</b></div>
        <div class="ig-stat">Style <b>{result.get('style','—')}</b></div>
    </div>
    """, unsafe_allow_html=True)

    # Download
    c1, c2, c3 = st.columns(3)
    with c1:
        if result.get("image_bytes"):
            st.download_button("⬇️ Download", data=result["image_bytes"],
                file_name=f"examhelp_{result.get('seed',0)}.png", mime="image/png",
                use_container_width=True, key=f"dl_{key_suffix}_{result.get('seed',0)}")
        else:
            st.markdown(
                f'<a href="{result["image_url"]}" target="_blank" '
                f'style="display:block;text-align:center;padding:8px;background:rgba(139,92,246,0.15);'
                f'border:1px solid rgba(139,92,246,0.3);border-radius:8px;color:#c4b5fd;'
                f'font-size:12px;text-decoration:none;">⬇️ Open Full Size</a>',
                unsafe_allow_html=True)
    with c2:
        if st.button("♻️ New Seed", use_container_width=True, key=f"regen_{key_suffix}_{result.get('seed',0)}"):
            st.session_state.ig_seed = random.randint(1, 2_147_483_647)
            st.session_state.ig_trigger = True
            st.rerun()
    with c3:
        # Step 9: Share button
        if st.button("🔗 Share URL", use_container_width=True, key=f"share_{key_suffix}_{result.get('seed',0)}"):
            st.session_state["ig_show_share"] = result.get("image_url", "")


# ── Step 9: Share box ───────────────────────────────────────────────────────
def _show_share():
    url = st.session_state.get("ig_show_share", "")
    if url:
        st.markdown(f"""
        <div class="share-box">
            🔗 <b>Shareable Link</b> — paste this URL anywhere:<br>
            <span style="color:#67e8f9">{url}</span>
        </div>
        """, unsafe_allow_html=True)
        st.text_input("Copy link:", value=url, key="ig_share_input", label_visibility="collapsed")
        if st.button("✖ Close", key="ig_share_close"):
            del st.session_state["ig_show_share"]
            st.rerun()


def render_image_generator():
    """Main entry point."""
    from image_generator_engine import (
        STYLE_PRESETS, ASPECT_RATIOS, POLLINATIONS_MODELS,
        generate_image, generate_batch,
        get_prompt_examples, get_random_prompt, get_categories, get_prompts_by_category,
        save_to_history, get_history, clear_history,
        build_share_url,
    )

    _header()

    # ── Init session state ──────────────────────────────────────────────────
    defaults = {
        "ig_style":   "🎨 Photorealistic",
        "ig_ratio":   "1:1 Square (1024×1024)",
        "ig_prompt":  "",
        "ig_negative": "",
        "ig_seed":    None,
        "ig_results": [],
        "ig_trigger": False,
        "ig_model_override": None,   # Step 6: manual model override
        "ig_show_share": "",
        "ig_history": [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # ── Tabs: Generate | Gallery | Models ──────────────────────────────────
    tab_gen, tab_gallery, tab_models = st.tabs(["🎨 Generate", "🖼️ Gallery", "🤖 Models"])

    # ══════════════════════════════════════════════════════════════════════
    # TAB 1 — GENERATE
    # ══════════════════════════════════════════════════════════════════════
    with tab_gen:
        left, right = st.columns([1, 1.3], gap="large")

        with left:
            # ── Step 10: Prompt with char count & random button ─────────
            st.markdown("### ✏️ Prompt")
            pc1, pc2 = st.columns([4, 1])
            with pc1:
                prompt = st.text_area(
                    "Prompt", value=st.session_state.ig_prompt, height=110,
                    placeholder="A majestic dragon soaring over a glowing neon city at midnight…",
                    key="ig_prompt_input", label_visibility="collapsed",
                )
                st.session_state.ig_prompt = prompt
                char_color = "#f87171" if len(prompt) > 400 else "rgba(255,255,255,.3)"
                st.markdown(f'<div class="char-count" style="color:{char_color}">{len(prompt)}/400 chars</div>',
                            unsafe_allow_html=True)
            with pc2:
                if st.button("🎲", help="Random prompt", key="ig_random"):
                    st.session_state.ig_prompt = get_random_prompt()
                    st.rerun()

            # ── Step 10: Category-filtered prompt picker ─────────────────
            with st.expander("💡 Browse Prompts by Category"):
                cats = get_categories()
                sel_cat = st.selectbox("Category", cats, key="ig_cat_select",
                                       label_visibility="collapsed")
                cat_prompts = get_prompts_by_category(sel_cat)
                for cp in cat_prompts:
                    if st.button(f"↗ {cp[:60]}…" if len(cp) > 60 else f"↗ {cp}",
                                 key=f"cp_{cp[:30]}", use_container_width=True):
                        st.session_state.ig_prompt = cp
                        st.rerun()

            # ── Style ────────────────────────────────────────────────────
            st.markdown("### 🎨 Style")
            style_names = list(STYLE_PRESETS.keys())
            sel_idx = style_names.index(st.session_state.ig_style) if st.session_state.ig_style in style_names else 0
            chosen_style = st.selectbox("Style", style_names, index=sel_idx,
                                        label_visibility="collapsed", key="ig_style_sel")
            st.session_state.ig_style = chosen_style
            preset = STYLE_PRESETS[chosen_style]
            st.markdown(
                f'<div class="ig-tip">🖌️ Model: <b>{preset["model"]}</b> · {preset["suffix"][:70]}…</div>',
                unsafe_allow_html=True)

            # ── Step 6: Optional manual model override ────────────────────
            with st.expander("⚙️ Advanced"):
                override_model = st.selectbox(
                    "Override Model (optional)",
                    ["Auto (use style default)"] + list(POLLINATIONS_MODELS.keys()),
                    key="ig_model_override_sel",
                )
                st.session_state.ig_model_override = (
                    None if override_model == "Auto (use style default)"
                    else override_model
                )

                ratio_names = list(ASPECT_RATIOS.keys())
                sel_r = ratio_names.index(st.session_state.ig_ratio) if st.session_state.ig_ratio in ratio_names else 0
                st.session_state.ig_ratio = st.selectbox(
                    "Aspect Ratio", ratio_names, index=sel_r, key="ig_ratio_sel")

                st.session_state.ig_negative = st.text_area(
                    "Negative Prompt",
                    value=st.session_state.ig_negative, height=60,
                    placeholder="blurry, low quality, watermark…", key="ig_neg")

                seed_val = st.number_input(
                    "Seed (0 = random)", min_value=0, max_value=2_147_483_647,
                    value=int(st.session_state.ig_seed or 0), key="ig_seed_inp")
                st.session_state.ig_seed = seed_val if seed_val != 0 else None

                batch_n = st.selectbox("Variations", [1, 2, 4], key="ig_batch_n")

            # ── Generate button ───────────────────────────────────────────
            st.markdown("")
            if st.button(f"🚀 Generate {'x' + str(batch_n) if batch_n > 1 else 'Image'}",
                         use_container_width=True, type="primary", key="ig_go"):
                if not st.session_state.ig_prompt.strip():
                    st.error("⚠️ Enter a prompt first!")
                else:
                    st.session_state.ig_trigger = True
                    st.session_state.ig_batch_n = batch_n
                    st.rerun()

            if st.button("← Back to Chat", use_container_width=True, key="ig_back"):
                st.session_state.app_mode = "chat"; st.rerun()

        # ── RIGHT: Canvas / Results ────────────────────────────────────
        with right:
            if st.session_state.ig_trigger:
                st.session_state.ig_trigger = False
                bn = st.session_state.get("ig_batch_n", 1)

                # Determine model
                style_model = STYLE_PRESETS.get(
                    st.session_state.ig_style, {}).get("model", "flux")
                final_model = st.session_state.ig_model_override or style_model

                with st.spinner(f"🎨 Generating with **{final_model}**… (~15-40s)"):
                    if bn > 1:
                        results = generate_batch(
                            prompt=st.session_state.ig_prompt,
                            style_preset=st.session_state.ig_style,
                            aspect_ratio=st.session_state.ig_ratio,
                            count=bn,
                        )
                    else:
                        r = generate_image(
                            prompt=st.session_state.ig_prompt,
                            style_preset=st.session_state.ig_style,
                            aspect_ratio=st.session_state.ig_ratio,
                            negative_prompt=st.session_state.ig_negative,
                            seed=st.session_state.ig_seed,
                        )
                        # Override model in URL if user picked one
                        if st.session_state.ig_model_override:
                            from image_generator_engine import get_pollinations_url
                            w, h = r["width"], r["height"]
                            r["image_url"] = get_pollinations_url(
                                r["prompt_used"], w, h,
                                st.session_state.ig_model_override, r["seed"])
                        results = [r]

                    st.session_state.ig_results = results
                    # Step 3: save to history
                    for res in results:
                        save_to_history(res, st.session_state)

            if st.session_state.ig_results:
                results = st.session_state.ig_results
                if len(results) == 1:
                    _show_image(results[0], "main")
                    _show_share()
                    with st.expander("📝 Full Prompt Used"):
                        st.code(results[0].get("prompt_used", ""), language=None)
                else:
                    for i in range(0, len(results), 2):
                        c1, c2 = st.columns(2)
                        for j, col in enumerate([c1, c2]):
                            idx = i + j
                            if idx < len(results):
                                with col:
                                    r = results[idx]
                                    if r.get("image_bytes"):
                                        st.image(r["image_bytes"], use_container_width=True,
                                                 caption=f"Variation {idx+1}")
                                        st.download_button(
                                            f"⬇️ #{idx+1}", data=r["image_bytes"],
                                            file_name=f"examhelp_v{idx+1}_{r['seed']}.png",
                                            mime="image/png", use_container_width=True,
                                            key=f"dl_b{idx}_{r['seed']}")
                                    elif r.get("image_url"):
                                        st.markdown(
                                            f'<img src="{r["image_url"]}" style="width:100%;border-radius:12px;" />',
                                            unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="ig-empty">
                    <div>
                        <span class="ig-empty-icon">🎨</span>
                        <div class="ig-empty-txt">YOUR IMAGE APPEARS HERE<br>
                        <span style="font-size:9px;opacity:.6;">Enter a prompt → Generate</span></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════
    # TAB 2 — GALLERY (Step 8)
    # ══════════════════════════════════════════════════════════════════════
    with tab_gallery:
        history = get_history(st.session_state)
        if not history:
            st.info("🖼️ No images generated yet. Create some in the Generate tab!")
        else:
            st.markdown(f"**{len(history)} images in your session gallery** (newest first)")
            if st.button("🗑️ Clear Gallery", key="ig_clear_hist"):
                clear_history(st.session_state)
                st.rerun()

            cols = st.columns(3)
            for i, entry in enumerate(history):
                with cols[i % 3]:
                    st.markdown('<div class="gal-item">', unsafe_allow_html=True)
                    st.markdown(
                        f'<img src="{entry["url"]}" style="width:100%;display:block;" />',
                        unsafe_allow_html=True)
                    st.markdown(
                        f'<div class="gal-meta">{entry["style"]}<br>'
                        f'<span style="opacity:.6">{entry["prompt"][:55]}…</span></div>',
                        unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("↗ Use Prompt", key=f"gal_use_{i}", use_container_width=True):
                            st.session_state.ig_prompt = entry["prompt"]
                            st.session_state.ig_style = entry["style"]
                            st.rerun()
                    with c2:
                        if st.button("🔗 Share", key=f"gal_share_{i}", use_container_width=True):
                            st.session_state["ig_show_share"] = entry["url"]
                            st.rerun()

            _show_share()

    # ══════════════════════════════════════════════════════════════════════
    # TAB 3 — MODELS (Step 6 expanded)
    # ══════════════════════════════════════════════════════════════════════
    with tab_models:
        st.markdown("### 🤖 All Available Free Models")
        st.markdown("All models are provided by **Pollinations.ai** — completely free, no API key needed.")
        st.markdown("")
        speed_color = {"fast": "#4ade80", "medium": "#facc15", "slow": "#60a5fa"}
        for model_id, info in POLLINATIONS_MODELS.items():
            col_info, col_try = st.columns([5, 1])
            with col_info:
                sc = speed_color.get(info["speed"], "#fff")
                st.markdown(
                    f'{info["icon"]} **{info["label"]}** `{model_id}` &nbsp;'
                    f'<span style="background:rgba(255,255,255,0.06);border:1px solid {sc}33;'
                    f'border-radius:100px;padding:2px 10px;font-size:10px;color:{sc};">'
                    f'{info["speed"].upper()}</span>',
                    unsafe_allow_html=True)
            with col_try:
                if st.button("Try", key=f"try_model_{model_id}", use_container_width=True):
                    st.session_state.ig_model_override = model_id
                    st.toast(f"Model set to {model_id} — go to Generate tab!", icon="✅")
            st.markdown("---")
