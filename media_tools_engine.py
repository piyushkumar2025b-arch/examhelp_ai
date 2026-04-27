"""
media_tools_engine.py
ExamHelp AI — Media Tools Suite
  Tab 1: AI Photo Editor (20+ effects)
  Tab 2: Image → PDF
  Tab 3: PDF → Any Format
  Tab 4: File QR Share (up to 10 MB)
"""
from __future__ import annotations
import base64, io, os, json, time, random, math
from typing import List, Optional, Tuple
import streamlit as st
from PIL import Image, ImageFilter, ImageEnhance, ImageOps, ImageDraw

try:
    import numpy as np
    _NP = True
except ImportError:
    _NP = False

try:
    import fitz
    _FITZ = True
except ImportError:
    _FITZ = False

try:
    import qrcode
    _QR = True
except ImportError:
    _QR = False

try:
    import requests as _req
    _REQ = True
except ImportError:
    _REQ = False

try:
    from docx import Document as _DocxDoc
    from docx.shared import Inches, Pt
    _DOCX = True
except ImportError:
    _DOCX = False

try:
    from rembg import remove as _rembg_remove
    _REMBG = True
except ImportError:
    _REMBG = False


# ═══════════════════════════════════════════════════════════
# CSS
# ═══════════════════════════════════════════════════════════
_MT_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;700&family=Syne:wght@700;800&display=swap');

.mt-hero {
    background: radial-gradient(ellipse at 20% 0%, rgba(99,102,241,0.18) 0%, transparent 60%),
                radial-gradient(ellipse at 80% 100%, rgba(6,182,212,0.14) 0%, transparent 60%),
                rgba(10,14,30,0.85);
    border: 1px solid rgba(99,102,241,0.22);
    border-radius: 24px; padding: 36px 28px 32px;
    margin-bottom: 24px; text-align: center;
    backdrop-filter: blur(20px);
    position: relative; overflow: hidden;
    animation: mtFadeUp 0.6s cubic-bezier(0.16,1,0.3,1) both;
}
.mt-hero::before {
    content:''; position:absolute; top:-1px; left:10%; right:10%; height:2px;
    background: linear-gradient(90deg, transparent, #6366f1, #06b6d4, transparent);
    border-radius:100px;
}
.mt-hero-title {
    font-family:'Syne',sans-serif; font-size:clamp(1.8rem,3.5vw,2.6rem); font-weight:800;
    background: linear-gradient(135deg,#fff 0%,#c7d2fe 30%,#818cf8 55%,#06b6d4 80%);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
    margin-bottom:10px; filter:drop-shadow(0 0 24px rgba(99,102,241,0.3));
}
.mt-hero-sub {
    font-size:0.95rem; color:rgba(255,255,255,0.5); max-width:580px; margin:0 auto;
    line-height:1.7;
}
@keyframes mtFadeUp {
    from{opacity:0;transform:translateY(20px);} to{opacity:1;transform:none;}
}

/* Filter button grid */
.mt-filter-btn {
    background: rgba(10,14,30,0.7);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px; padding: 10px 8px;
    text-align: center; cursor: pointer;
    transition: all 0.25s ease;
    font-size: 0.75rem; color: rgba(255,255,255,0.7);
}
.mt-filter-btn:hover, .mt-filter-btn.active {
    border-color: rgba(99,102,241,0.5);
    background: rgba(99,102,241,0.1);
    color: #c7d2fe; transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(99,102,241,0.15);
}
.mt-filter-icon { font-size:1.4rem; display:block; margin-bottom:4px; }

/* Section header */
.mt-sec {
    display:flex; align-items:center; gap:10px; margin:20px 0 12px;
}
.mt-sec-line { flex:1; height:1px; background:linear-gradient(90deg,rgba(99,102,241,0.4),transparent); }
.mt-sec-label {
    font-family:'JetBrains Mono',monospace; font-size:0.62rem;
    letter-spacing:3px; color:#818cf8; text-transform:uppercase; white-space:nowrap;
}

/* Effect card */
.mt-fx-btn {
    position:relative; overflow:hidden;
    background:rgba(10,14,30,0.7); border:1px solid rgba(255,255,255,0.07);
    border-radius:14px; padding:14px 10px; text-align:center; cursor:pointer;
    transition:all 0.3s cubic-bezier(0.16,1,0.3,1);
}
.mt-fx-btn:hover { transform:translateY(-4px); border-color:rgba(99,102,241,0.45);
    box-shadow:0 12px 36px rgba(0,0,0,0.35); }
.mt-fx-icon { font-size:1.8rem; display:block; margin-bottom:6px; }
.mt-fx-label { font-size:0.7rem; font-weight:700; color:rgba(255,255,255,0.75); }

/* QR result card */
.mt-qr-card {
    background: linear-gradient(135deg,rgba(99,102,241,0.1),rgba(6,182,212,0.07));
    border: 1px solid rgba(99,102,241,0.25);
    border-radius: 20px; padding: 24px; text-align:center;
    animation: mtFadeUp 0.5s both;
}
.mt-qr-link {
    font-family:'JetBrains Mono',monospace; font-size:0.82rem;
    color:#a5f3fc; word-break:break-all; background:rgba(6,182,212,0.08);
    border:1px solid rgba(6,182,212,0.2); border-radius:10px;
    padding:10px 14px; display:block; margin:14px 0;
}
.mt-info-chip {
    display:inline-flex; align-items:center; gap:6px;
    background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.08);
    border-radius:100px; padding:5px 14px; font-size:0.75rem;
    color:rgba(255,255,255,0.45); margin:4px;
}

/* Palette swatch */
.mt-swatch {
    display:inline-block; width:40px; height:40px;
    border-radius:8px; margin:4px;
    border:1px solid rgba(255,255,255,0.1);
    box-shadow:0 4px 12px rgba(0,0,0,0.3);
    transition:transform 0.2s ease;
}
.mt-swatch:hover { transform:scale(1.1); }

/* Stat tile */
.mt-stat { background:rgba(10,14,30,0.8); border:1px solid rgba(255,255,255,0.07);
    border-radius:14px; padding:14px; text-align:center; }
.mt-stat-n { font-family:'Syne',sans-serif; font-size:1.4rem; font-weight:800;
    color:#818cf8; }
.mt-stat-l { font-size:0.6rem; letter-spacing:2px; color:rgba(255,255,255,0.3);
    text-transform:uppercase; font-family:'JetBrains Mono',monospace; }
</style>
"""

# ═══════════════════════════════════════════════════════════
# PHOTO FILTER & EFFECT FUNCTIONS
# ═══════════════════════════════════════════════════════════

def _to_np(img):
    return np.array(img.convert("RGB"), dtype=np.float32)

def _from_np(arr):
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

def _apply_filter(img, name):
    img = img.convert("RGB")
    if name == "Original": return img
    if name == "Grayscale": return ImageOps.grayscale(img).convert("RGB")
    if name == "Sepia":
        if _NP:
            a=_to_np(img)
            return _from_np(np.stack([
                np.clip(a[:,:,0]*0.393+a[:,:,1]*0.769+a[:,:,2]*0.189,0,255),
                np.clip(a[:,:,0]*0.349+a[:,:,1]*0.686+a[:,:,2]*0.168,0,255),
                np.clip(a[:,:,0]*0.272+a[:,:,1]*0.534+a[:,:,2]*0.131,0,255)
            ],axis=2))
        return ImageEnhance.Color(img).enhance(0.3)
    if name == "Vintage":
        img=ImageEnhance.Color(ImageEnhance.Contrast(img).enhance(0.85)).enhance(0.7)
        if _NP:
            a=_to_np(img); a[:,:,0]=np.clip(a[:,:,0]*1.1,0,255); a[:,:,2]=np.clip(a[:,:,2]*0.8,0,255)
            return _from_np(a)
        return img
    if name == "Noir": return ImageOps.autocontrast(ImageOps.grayscale(img),10).convert("RGB")
    if name == "Vivid": return ImageEnhance.Contrast(ImageEnhance.Color(img).enhance(2.0)).enhance(1.2)
    if name == "Cool":
        if _NP:
            a=_to_np(img); a[:,:,0]=np.clip(a[:,:,0]*0.85,0,255); a[:,:,2]=np.clip(a[:,:,2]*1.15,0,255)
            return _from_np(a)
        return img
    if name == "Warm":
        if _NP:
            a=_to_np(img); a[:,:,0]=np.clip(a[:,:,0]*1.15,0,255); a[:,:,2]=np.clip(a[:,:,2]*0.85,0,255)
            return _from_np(a)
        return img
    if name == "Fade": return ImageEnhance.Contrast(ImageEnhance.Color(img).enhance(0.5)).enhance(0.75)
    if name == "Duotone":
        if _NP:
            gray=np.array(ImageOps.grayscale(img),dtype=np.float32)/255.0
            return _from_np(np.stack([gray*99,gray*102,gray*241],axis=2))
        return img
    if name == "Sunset":
        if _NP:
            a=_to_np(img); a[:,:,0]=np.clip(a[:,:,0]*1.2,0,255); a[:,:,2]=np.clip(a[:,:,2]*0.7,0,255)
            return _from_np(a)
        return img
    if name == "Forest":
        if _NP:
            a=_to_np(img); a[:,:,1]=np.clip(a[:,:,1]*1.15,0,255); a[:,:,0]=np.clip(a[:,:,0]*0.9,0,255)
            return _from_np(a)
        return img
    if name == "Cyberpunk":
        if _NP:
            a=_to_np(img)
            a[:,:,0]=np.clip(a[:,:,0]*1.3,0,255); a[:,:,2]=np.clip(a[:,:,2]*1.4,0,255); a[:,:,1]=np.clip(a[:,:,1]*0.7,0,255)
            return _from_np(a)
        return img
    if name == "Film":
        img=ImageEnhance.Color(ImageEnhance.Contrast(img).enhance(1.1)).enhance(0.85)
        if _NP:
            return _from_np(_to_np(img)+np.random.normal(0,6,np.array(img).shape).astype(np.float32))
        return img
    return img

def _fx_enhance(img): return ImageEnhance.Brightness(ImageEnhance.Color(ImageEnhance.Contrast(ImageEnhance.Sharpness(img).enhance(1.5)).enhance(1.15)).enhance(1.2)).enhance(1.05)
def _fx_hdr(img): return ImageEnhance.Color(ImageEnhance.Sharpness(ImageEnhance.Contrast(img).enhance(1.4)).enhance(2.0)).enhance(1.5)

def _fx_vignette(img):
    if not _NP: return img
    w,h=img.size; a=_to_np(img)
    X=np.linspace(-1,1,w); Y=np.linspace(-1,1,h)
    Xg,Yg=np.meshgrid(X,Y)
    return _from_np(a*np.clip(1.0-(Xg**2+Yg**2)*0.7,0.2,1.0)[:,:,np.newaxis])

def _fx_tiltshift(img):
    w,h=img.size; bl=img.filter(ImageFilter.GaussianBlur(8))
    mask=Image.new("L",(w,h),0); draw=ImageDraw.Draw(mask)
    cy,fh=h//2,h//5
    for y in range(h):
        d=abs(y-cy)
        v=255 if d<fh else max(0,int(255*(1-(d-fh)/fh))) if d<fh*2 else 0
        draw.line([(0,y),(w,y)],fill=v)
    return Image.composite(img,bl,mask)

def _fx_sketch(img):
    if not _NP: return ImageOps.grayscale(img).convert("RGB")
    gray=np.array(ImageOps.grayscale(img),dtype=np.float32)
    blur=np.array(Image.fromarray((255-gray).astype(np.uint8)).filter(ImageFilter.GaussianBlur(20)),dtype=np.float32)
    return Image.fromarray(np.clip(gray*255/(255-blur+1),0,255).astype(np.uint8)).convert("RGB")

def _fx_glitch(img):
    if not _NP: return img
    a=np.array(img.convert("RGB")); r=a.copy()
    r[:,:,0]=np.roll(a[:,:,0],random.randint(6,18),axis=1)
    for _ in range(random.randint(4,8)):
        y=random.randint(0,a.shape[0]-5)
        r[y:y+random.randint(2,6)]=np.roll(r[y:y+random.randint(2,6)],random.randint(-25,25),axis=1)
    return Image.fromarray(r)

def _fx_chromatic(img,s=6):
    if not _NP: return img
    a=np.array(img.convert("RGB")); r=a.copy()
    r[:,s:,0]=a[:,:-s,0]; r[:,:-s,2]=a[:,s:,2]
    return Image.fromarray(r)

def _fx_grain(img):
    if not _NP: return img
    return _from_np(_to_np(img)+np.random.normal(0,14,np.array(img).shape).astype(np.float32))

def _fx_dreamy(img):
    soft=img.filter(ImageFilter.GaussianBlur(3))
    if _NP: return _from_np(np.clip(_to_np(img)*0.6+_to_np(soft)*0.55,0,255))
    return soft

def _fx_neon(img):
    if not _NP: return img
    e=img.filter(ImageFilter.FIND_EDGES); ea=_to_np(e)
    ea[:,:,0]*=3; ea[:,:,1]*=2; ea[:,:,2]*=4
    return _from_np(np.clip(ea*2.5,0,255))

def _extract_palette(img,n=8):
    pixels=list(img.resize((80,80)).convert("RGB").getdata()); random.shuffle(pixels)
    colors=[]; seen=set()
    for r,g,b in pixels[:400]:
        hx=f"#{r:02x}{g:02x}{b:02x}"
        if hx not in seen: seen.add(hx); colors.append(hx)
        if len(colors)>=n: break
    return colors

def _img_to_bytes(img,fmt="PNG",quality=90):
    buf=io.BytesIO()
    img.convert("RGB").save(buf,format="JPEG" if fmt=="JPG" else fmt,**( {"quality":quality} if fmt in ("JPG","JPEG") else {}))
    return buf.getvalue()


# ═══════════════════════════════════════════════════════════
# TAB 1 — AI PHOTO EDITOR
# ═══════════════════════════════════════════════════════════

_FILTERS = ["Original","Grayscale","Sepia","Vintage","Noir","Vivid",
            "Cool","Warm","Fade","Duotone","Sunset","Forest","Cyberpunk","Film"]

_FX = [
    ("✨","AI Enhance","enhance"),("🌅","HDR Effect","hdr"),
    ("🌑","Vignette","vignette"),("🔭","Tilt-Shift","tiltshift"),
    ("✏️","Sketch","sketch"),("⚡","Glitch","glitch"),
    ("🌈","Chromatic","chromatic"),("🎞️","Film Grain","grain"),
    ("💭","Dreamy","dreamy"),("🌟","Neon","neon"),
]

def _render_photo_editor():
    st.markdown("""
    <div class="mt-sec">
        <span class="mt-sec-label">🎨 AI Photo Editor</span>
        <div class="mt-sec-line"></div>
    </div>
    """, unsafe_allow_html=True)

    up = st.file_uploader("Upload Image", type=["png","jpg","jpeg","webp","bmp"],
                          key="mt_photo_up", label_visibility="collapsed")
    if not up:
        st.markdown("""
        <div style="border:2px dashed rgba(99,102,241,0.3);border-radius:18px;padding:44px;text-align:center;">
            <div style="font-size:3rem;margin-bottom:12px;">🖼️</div>
            <div style="color:rgba(255,255,255,0.5);font-size:0.9rem;">Drop an image to start editing</div>
            <div style="color:rgba(255,255,255,0.25);font-size:0.75rem;margin-top:6px;">PNG · JPG · WEBP · BMP</div>
        </div>
        """, unsafe_allow_html=True)
        return

    orig = Image.open(up)
    ck = f"mt_orig_{up.name}_{up.size}"
    if st.session_state.get("mt_img_ck") != ck:
        st.session_state.mt_img_ck = ck
        st.session_state.mt_img = orig.copy()
        st.session_state.mt_filter = "Original"
        st.session_state.mt_brightness = 1.0
        st.session_state.mt_contrast = 1.0
        st.session_state.mt_saturation = 1.0
        st.session_state.mt_sharpness = 1.0
        st.session_state.mt_blur = 0

    # ── Show original + preview side-by-side ──
    c1, c2 = st.columns(2)
    with c1:
        st.caption("📷 Original")
        st.image(orig, use_container_width=True)
    with c2:
        st.caption("✨ Preview")
        preview_ph = st.empty()

    # ── Filter Gallery ──
    st.markdown("""<div class="mt-sec"><span class="mt-sec-label">🎨 Filters</span><div class="mt-sec-line"></div></div>""", unsafe_allow_html=True)
    fcols = st.columns(7)
    chosen_filter = st.session_state.get("mt_filter","Original")
    for i, f in enumerate(_FILTERS):
        with fcols[i % 7]:
            if st.button(f, key=f"mt_f_{f}", use_container_width=True,
                         type="primary" if chosen_filter==f else "secondary"):
                st.session_state.mt_filter = f
                st.rerun()

    # ── Adjustments ──
    st.markdown("""<div class="mt-sec"><span class="mt-sec-label">⚙️ Adjustments</span><div class="mt-sec-line"></div></div>""", unsafe_allow_html=True)
    a1,a2,a3,a4,a5 = st.columns(5)
    with a1: br = st.slider("☀️ Brightness", 0.1, 3.0, st.session_state.get("mt_brightness",1.0), 0.05, key="mt_br")
    with a2: co = st.slider("🎭 Contrast",   0.1, 3.0, st.session_state.get("mt_contrast",1.0),   0.05, key="mt_co")
    with a3: sa = st.slider("🌈 Saturation", 0.0, 3.0, st.session_state.get("mt_saturation",1.0), 0.05, key="mt_sa")
    with a4: sh = st.slider("🔪 Sharpness",  0.0, 5.0, st.session_state.get("mt_sharpness",1.0),  0.1,  key="mt_sh")
    with a5: bl = st.slider("💨 Blur",        0,   12,  st.session_state.get("mt_blur",0),          1,    key="mt_bl")

    # ── AI Effects ──
    st.markdown("""<div class="mt-sec"><span class="mt-sec-label">⚡ AI & Creative Effects</span><div class="mt-sec-line"></div></div>""", unsafe_allow_html=True)
    ec = st.columns(5)
    chosen_fx = None
    for i,(icon,label,fid) in enumerate(_FX):
        with ec[i%5]:
            if st.button(f"{icon} {label}", key=f"mt_fx_{fid}", use_container_width=True):
                chosen_fx = fid

    # ── Transforms ──
    st.markdown("""<div class="mt-sec"><span class="mt-sec-label">🔄 Transform</span><div class="mt-sec-line"></div></div>""", unsafe_allow_html=True)
    t1,t2,t3,t4,t5 = st.columns(5)
    do_rot90 = t1.button("↻ 90°",  key="mt_rot90",  use_container_width=True)
    do_rot180= t2.button("↺ 180°", key="mt_rot180", use_container_width=True)
    do_fh    = t3.button("↔ Flip H",key="mt_fh",    use_container_width=True)
    do_fv    = t4.button("↕ Flip V",key="mt_fv",    use_container_width=True)
    do_mirror= t5.button("🪞 Mirror",key="mt_mirror",use_container_width=True)

    wr1,wr2 = st.columns(2)
    with wr1:
        nw = st.number_input("Width px",  value=orig.width,  min_value=50, max_value=4000, step=10, key="mt_nw")
    with wr2:
        nh = st.number_input("Height px", value=orig.height, min_value=50, max_value=4000, step=10, key="mt_nh")
    do_resize = st.button("📐 Apply Resize", key="mt_resize", use_container_width=True)

    # ── Watermark ──
    st.markdown("""<div class="mt-sec"><span class="mt-sec-label">🖊️ Watermark</span><div class="mt-sec-line"></div></div>""", unsafe_allow_html=True)
    wm1,wm2,wm3 = st.columns(3)
    wm_text  = wm1.text_input("Watermark text", placeholder="© ExamHelp AI", key="mt_wm_txt")
    wm_pos   = wm2.selectbox("Position", ["Bottom-Right","Bottom-Left","Top-Right","Top-Left","Center"], key="mt_wm_pos")
    wm_alpha = wm3.slider("Opacity", 0.1, 1.0, 0.5, 0.05, key="mt_wm_alpha")
    do_wm = st.button("💧 Add Watermark", key="mt_add_wm", use_container_width=True)

    # ── Color Palette ──
    do_palette = st.button("🎨 Extract Color Palette", key="mt_palette", use_container_width=True)

    # ── Build edited image ──
    edited = st.session_state.mt_img.copy()
    edited = _apply_filter(edited, st.session_state.mt_filter)
    if br != 1.0: edited = ImageEnhance.Brightness(edited).enhance(br)
    if co != 1.0: edited = ImageEnhance.Contrast(edited).enhance(co)
    if sa != 1.0: edited = ImageEnhance.Color(edited).enhance(sa)
    if sh != 1.0: edited = ImageEnhance.Sharpness(edited).enhance(sh)
    if bl > 0:    edited = edited.filter(ImageFilter.GaussianBlur(radius=bl))

    # Apply AI effect
    FX_MAP = {"enhance":_fx_enhance,"hdr":_fx_hdr,"vignette":_fx_vignette,
              "tiltshift":_fx_tiltshift,"sketch":_fx_sketch,"glitch":_fx_glitch,
              "chromatic":_fx_chromatic,"grain":_fx_grain,"dreamy":_fx_dreamy,"neon":_fx_neon}
    if chosen_fx and chosen_fx in FX_MAP:
        with st.spinner(f"Applying {chosen_fx}..."):
            edited = FX_MAP[chosen_fx](edited)
        st.session_state.mt_img = edited

    # Apply transforms
    if do_rot90:   st.session_state.mt_img = edited.rotate(-90, expand=True); st.rerun()
    if do_rot180:  st.session_state.mt_img = edited.rotate(180);              st.rerun()
    if do_fh:      st.session_state.mt_img = ImageOps.mirror(edited);         st.rerun()
    if do_fv:      st.session_state.mt_img = ImageOps.flip(edited);           st.rerun()
    if do_mirror:  st.session_state.mt_img = ImageOps.mirror(edited);         st.rerun()
    if do_resize:  st.session_state.mt_img = edited.resize((int(nw),int(nh)), Image.LANCZOS); st.rerun()

    # Watermark
    if do_wm and wm_text:
        e2 = edited.convert("RGBA")
        overlay = Image.new("RGBA", e2.size, (255,255,255,0))
        draw = ImageDraw.Draw(overlay)
        tw, th = e2.size[0]//6, e2.size[1]//30
        pos_map = {
            "Bottom-Right": (e2.size[0]-tw*len(wm_text)-10, e2.size[1]-th*4),
            "Bottom-Left":  (10, e2.size[1]-th*4),
            "Top-Right":    (e2.size[0]-tw*len(wm_text)-10, 10),
            "Top-Left":     (10, 10),
            "Center":       (e2.size[0]//2-tw*len(wm_text)//2, e2.size[1]//2),
        }
        xy = pos_map.get(wm_pos, (10,10))
        draw.text(xy, wm_text, fill=(255,255,255,int(255*wm_alpha)))
        edited = Image.alpha_composite(e2, overlay).convert("RGB")
        st.session_state.mt_img = edited
        st.rerun()

    # Color Palette
    if do_palette:
        palette = _extract_palette(edited)
        swatches = "".join(f'<span class="mt-swatch" style="background:{c};" title="{c}"></span>' for c in palette)
        st.markdown(f"""
        <div style="background:rgba(10,14,30,0.8);border:1px solid rgba(255,255,255,0.07);
            border-radius:16px;padding:20px;margin-top:12px;">
            <div class="mt-sec-label" style="margin-bottom:12px;">🎨 Extracted Palette</div>
            <div>{swatches}</div>
            <div style="margin-top:12px;font-family:'JetBrains Mono',monospace;font-size:0.72rem;color:rgba(255,255,255,0.3);">
                {" · ".join(palette)}
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Show preview
    preview_ph.image(edited, use_container_width=True)

    # ── Export ──
    st.markdown("""<div class="mt-sec"><span class="mt-sec-label">📥 Export</span><div class="mt-sec-line"></div></div>""", unsafe_allow_html=True)
    ex1,ex2,ex3,ex4 = st.columns(4)
    fmt_map = {"PNG":"PNG","JPG":"JPG","WEBP":"WEBP","BMP":"BMP"}
    for col,(fmt,fmtk) in zip([ex1,ex2,ex3,ex4],fmt_map.items()):
        with col:
            st.download_button(f"⬇️ {fmt}", _img_to_bytes(edited,fmtk),
                               f"edited.{fmt.lower()}", f"image/{fmt.lower()}",
                               use_container_width=True, key=f"mt_dl_{fmt}")

# ═══════════════════════════════════════════════════════════
# TAB 2 — IMAGE → PDF
# ═══════════════════════════════════════════════════════════

def _render_image_to_pdf():
    st.markdown("""<div class="mt-sec"><span class="mt-sec-label">🖼️ Image → PDF Converter</span><div class="mt-sec-line"></div></div>""", unsafe_allow_html=True)

    files = st.file_uploader("Upload Images (multiple OK)", type=["png","jpg","jpeg","webp","bmp"],
                              accept_multiple_files=True, key="mt_img2pdf_up", label_visibility="collapsed")
    if not files:
        st.markdown("""
        <div style="border:2px dashed rgba(6,182,212,0.3);border-radius:18px;padding:40px;text-align:center;">
            <div style="font-size:3rem;margin-bottom:12px;">🖼️→📄</div>
            <div style="color:rgba(255,255,255,0.5);">Upload one or more images to convert to PDF</div>
        </div>""", unsafe_allow_html=True)
        return

    st.success(f"✅ {len(files)} image(s) loaded")

    # Preview thumbnails
    thumb_cols = st.columns(min(len(files), 6))
    images = []
    for i, f in enumerate(files):
        img = Image.open(f).convert("RGB")
        images.append(img)
        with thumb_cols[i % 6]:
            st.image(img, caption=f.name[:15], use_container_width=True)

    # Options
    c1,c2,c3 = st.columns(3)
    page_size = c1.selectbox("Page Size", ["A4","Letter","A3","A5","Same as image"], key="mt_i2p_size")
    orient    = c2.selectbox("Orientation", ["Portrait","Landscape"], key="mt_i2p_orient")
    quality   = c3.slider("JPEG Quality", 50, 100, 85, key="mt_i2p_q")
    fit_mode  = st.selectbox("Fit Mode", ["Fit to page (keep ratio)","Stretch to fill","Original size"], key="mt_i2p_fit")

    if st.button("📄 Convert to PDF", type="primary", use_container_width=True, key="mt_i2p_btn"):
        with st.spinner("Converting images to PDF..."):
            buf = io.BytesIO()
            PAGE_SIZES = {"A4":(595,842),"Letter":(612,792),"A3":(842,1191),"A5":(420,595)}

            if page_size == "Same as image":
                pw,ph = images[0].size
            else:
                pw,ph = PAGE_SIZES.get(page_size,(595,842))
                if orient == "Landscape": pw,ph = ph,pw

            processed = []
            for img in images:
                img = img.convert("RGB")
                if page_size != "Same as image":
                    if fit_mode.startswith("Fit"):
                        img.thumbnail((pw,ph), Image.LANCZOS)
                        bg = Image.new("RGB",(pw,ph),(255,255,255))
                        offset=((pw-img.width)//2,(ph-img.height)//2)
                        bg.paste(img, offset)
                        img = bg
                    elif fit_mode.startswith("Stretch"):
                        img = img.resize((pw,ph), Image.LANCZOS)
                processed.append(img)

            processed[0].save(buf, format="PDF", save_all=True,
                              append_images=processed[1:], quality=quality)
            pdf_bytes = buf.getvalue()

        st.success(f"✅ PDF created! ({len(pdf_bytes)//1024} KB, {len(images)} pages)")
        st.download_button("⬇️ Download PDF", pdf_bytes, "images_converted.pdf",
                           "application/pdf", use_container_width=True, key="mt_i2p_dl")


# ═══════════════════════════════════════════════════════════
# TAB 3 — PDF → ANY FORMAT
# ═══════════════════════════════════════════════════════════

def _render_pdf_converter():
    st.markdown("""<div class="mt-sec"><span class="mt-sec-label">📄 PDF → Any Format</span><div class="mt-sec-line"></div></div>""", unsafe_allow_html=True)

    pdf_file = st.file_uploader("Upload PDF", type=["pdf"], key="mt_pdf_conv_up", label_visibility="collapsed")
    if not pdf_file:
        st.markdown("""
        <div style="border:2px dashed rgba(139,92,246,0.3);border-radius:18px;padding:40px;text-align:center;">
            <div style="font-size:3rem;margin-bottom:12px;">📄→🔀</div>
            <div style="color:rgba(255,255,255,0.5);">Upload a PDF to convert to another format</div>
        </div>""", unsafe_allow_html=True)
        return

    fmt = st.selectbox("Convert to:", ["Images (PNG)","Images (JPG)","Plain Text (.txt)",
                                        "Word Document (.docx)","HTML","Markdown (.md)"],
                        key="mt_pdf_fmt")
    dpi = st.slider("Resolution (DPI) — for image exports", 72, 300, 150, key="mt_pdf_dpi") if "Image" in fmt else 150

    if not st.button("🔀 Convert", type="primary", use_container_width=True, key="mt_pdf_conv_btn"):
        return

    if not _FITZ:
        st.error("PyMuPDF not installed. Run: pip install pymupdf"); return

    raw = pdf_file.read()
    doc = fitz.open(stream=raw, filetype="pdf")
    pg_count = doc.page_count

    with st.spinner(f"Converting {pg_count} page(s)..."):

        if "Images (PNG)" in fmt or "Images (JPG)" in fmt:
            ext = "jpg" if "JPG" in fmt else "png"
            import zipfile
            zip_buf = io.BytesIO()
            with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
                for i, page in enumerate(doc):
                    mat = fitz.Matrix(dpi/72, dpi/72)
                    pix = page.get_pixmap(matrix=mat)
                    img_bytes = pix.tobytes(output=ext)
                    zf.writestr(f"page_{i+1:03d}.{ext}", img_bytes)
            zip_buf.seek(0)
            st.success(f"✅ {pg_count} pages converted!")
            st.download_button(f"⬇️ Download ZIP ({ext.upper()}s)", zip_buf.getvalue(),
                               f"pdf_pages.zip","application/zip", use_container_width=True, key="mt_pdf_dl_img")

        elif "Text" in fmt:
            txt = "\n\n".join(f"--- Page {i+1} ---\n{doc[i].get_text()}" for i in range(pg_count))
            st.success(f"✅ {len(txt.split())} words extracted!")
            st.text_area("Preview (first 2000 chars)", txt[:2000], height=200, key="mt_pdf_txt_prev")
            st.download_button("⬇️ Download TXT", txt.encode(), "pdf_text.txt",
                               "text/plain", use_container_width=True, key="mt_pdf_dl_txt")

        elif "Word" in fmt:
            if not _DOCX:
                st.error("python-docx not installed. Run: pip install python-docx"); return
            doc_word = _DocxDoc()
            doc_word.add_heading(pdf_file.name.replace(".pdf",""), 0)
            for i in range(pg_count):
                doc_word.add_heading(f"Page {i+1}", level=2)
                for para in doc[i].get_text().split("\n"):
                    if para.strip():
                        doc_word.add_paragraph(para.strip())
                doc_word.add_page_break()
            wbuf = io.BytesIO(); doc_word.save(wbuf)
            st.success("✅ Word document created!")
            st.download_button("⬇️ Download DOCX", wbuf.getvalue(), "pdf_converted.docx",
                               "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                               use_container_width=True, key="mt_pdf_dl_docx")

        elif "HTML" in fmt:
            pages_html = []
            for i in range(pg_count):
                pages_html.append(f"<section><h2>Page {i+1}</h2>{doc[i].get_text('html')}</section>")
            html_out = f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>{pdf_file.name}</title></head><body>{''.join(pages_html)}</body></html>"
            st.success("✅ HTML created!")
            st.download_button("⬇️ Download HTML", html_out.encode(), "pdf_converted.html",
                               "text/html", use_container_width=True, key="mt_pdf_dl_html")

        elif "Markdown" in fmt:
            lines = []
            for i in range(pg_count):
                lines.append(f"\n## Page {i+1}\n")
                for ln in doc[i].get_text().split("\n"):
                    lines.append(ln)
            md_out = "\n".join(lines)
            st.success("✅ Markdown created!")
            st.download_button("⬇️ Download MD", md_out.encode(), "pdf_converted.md",
                               "text/markdown", use_container_width=True, key="mt_pdf_dl_md")

# ═══════════════════════════════════════════════════════════
# TAB 4 — FILE QR SHARE (upload → file.io → QR code)
# ═══════════════════════════════════════════════════════════

MAX_FILE_BYTES = 10 * 1024 * 1024  # 10 MB

def _upload_fileio(file_bytes: bytes, filename: str, expiry: str = "14d") -> dict:
    """Upload file to file.io and return response dict."""
    import urllib.request, urllib.parse
    boundary = f"----FormBoundary{random.randint(100000,999999)}"
    body_parts = []
    body_parts.append(f"--{boundary}\r\n".encode())
    body_parts.append(f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode())
    body_parts.append(b"Content-Type: application/octet-stream\r\n\r\n")
    body_parts.append(file_bytes)
    body_parts.append(f"\r\n--{boundary}--\r\n".encode())
    body = b"".join(body_parts)
    url = f"https://file.io/?expires={expiry}&autoDelete=true"
    req = urllib.request.Request(url, data=body,
          headers={"Content-Type": f"multipart/form-data; boundary={boundary}",
                   "User-Agent": "ExamHelp/1.0"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"success": False, "error": str(e)}


def _make_qr(url: str) -> bytes:
    """Generate a styled QR code PNG."""
    if not _QR:
        return b""
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H,
                        box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#6366f1", back_color="white")
    buf = io.BytesIO(); img.save(buf, format="PNG")
    return buf.getvalue()


def _render_file_qr_share():
    st.markdown("""<div class="mt-sec"><span class="mt-sec-label">🔗 File QR Share — Upload & Get Link</span><div class="mt-sec-line"></div></div>""", unsafe_allow_html=True)

    st.markdown("""
    <div style="background:linear-gradient(135deg,rgba(99,102,241,0.08),rgba(6,182,212,0.05));
        border:1px solid rgba(99,102,241,0.2);border-radius:16px;padding:16px 20px;margin-bottom:20px;">
        <div style="display:flex;gap:16px;flex-wrap:wrap;">
            <span class="mt-info-chip">📁 Any file type</span>
            <span class="mt-info-chip">⚖️ Up to 10 MB</span>
            <span class="mt-info-chip">⏳ Expires in 14 days</span>
            <span class="mt-info-chip">🔒 Auto-delete after download</span>
            <span class="mt-info-chip">🆓 Powered by file.io (free)</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    up = st.file_uploader("Upload any file (max 10 MB)", key="mt_qr_file", label_visibility="collapsed")
    expiry = st.selectbox("Link expires after:", ["1d","3d","7d","14d","1w","1m"], index=3, key="mt_qr_expiry")

    if not up:
        st.markdown("""
        <div style="border:2px dashed rgba(99,102,241,0.3);border-radius:18px;padding:44px;text-align:center;">
            <div style="font-size:3.5rem;margin-bottom:14px;">📁</div>
            <div style="color:rgba(255,255,255,0.5);font-size:0.9rem;">Upload any file up to <strong style="color:#818cf8;">10 MB</strong></div>
            <div style="color:rgba(255,255,255,0.25);font-size:0.75rem;margin-top:8px;">PDF · DOCX · ZIP · MP4 · PNG · Any format</div>
        </div>""", unsafe_allow_html=True)
        return

    # Size check
    file_bytes = up.read()
    size_kb = len(file_bytes) / 1024
    size_mb = size_kb / 1024

    # Show file info
    c1,c2,c3 = st.columns(3)
    c1.markdown(f'<div class="mt-stat"><div class="mt-stat-n">{size_mb:.2f}</div><div class="mt-stat-l">MB</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="mt-stat"><div class="mt-stat-n">{up.name.split(".")[-1].upper()}</div><div class="mt-stat-l">Type</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="mt-stat"><div class="mt-stat-n">{up.name[:14]}</div><div class="mt-stat-l">Filename</div></div>', unsafe_allow_html=True)

    if len(file_bytes) > MAX_FILE_BYTES:
        st.error(f"❌ File is {size_mb:.2f} MB. Maximum allowed is 10 MB.")
        return

    if st.button("🚀 Upload & Generate QR Code", type="primary", use_container_width=True, key="mt_qr_upload_btn"):
        prog = st.progress(0, "Uploading to secure server...")
        for pct in range(0, 60, 10):
            time.sleep(0.1); prog.progress(pct, f"Uploading... {pct}%")

        with st.spinner("⬆️ Uploading file..."):
            result = _upload_fileio(file_bytes, up.name, expiry)

        prog.progress(90, "Generating QR code...")

        if not result.get("success"):
            prog.empty()
            st.error(f"❌ Upload failed: {result.get('error','Unknown error')}")
            st.info("💡 Try: check your internet connection, or try a smaller file.")
            return

        link = result.get("link","")
        qr_bytes = _make_qr(link)
        prog.progress(100, "Done!")
        time.sleep(0.3); prog.empty()

        # Show result
        st.markdown(f"""
        <div class="mt-qr-card">
            <div style="font-size:2rem;margin-bottom:8px;">🎉</div>
            <div style="font-family:'Syne',sans-serif;font-size:1.3rem;font-weight:800;color:#fff;margin-bottom:6px;">
                File Uploaded Successfully!
            </div>
            <div style="color:rgba(255,255,255,0.5);font-size:0.85rem;margin-bottom:16px;">
                Share the QR code or link below. Anyone who scans it can download your file.
            </div>
            <span class="mt-qr-link">{link}</span>
            <div style="display:flex;gap:8px;flex-wrap:wrap;justify-content:center;margin-bottom:16px;">
                <span class="mt-info-chip">⏳ Expires: {expiry}</span>
                <span class="mt-info-chip">📁 {up.name}</span>
                <span class="mt-info-chip">⚖️ {size_mb:.2f} MB</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if qr_bytes:
            qr_col, info_col = st.columns([1,1])
            with qr_col:
                st.image(qr_bytes, caption="📱 Scan to download file", use_container_width=True)
                st.download_button("⬇️ Save QR Code", qr_bytes, "file_qr.png",
                                   "image/png", use_container_width=True, key="mt_qr_dl_qr")
            with info_col:
                st.markdown(f"""
                <div style="padding:20px;background:rgba(10,14,30,0.8);border:1px solid rgba(255,255,255,0.07);
                    border-radius:16px;height:100%;">
                    <div style="font-family:'JetBrains Mono',monospace;font-size:0.65rem;letter-spacing:3px;
                        color:#818cf8;text-transform:uppercase;margin-bottom:16px;">How to use</div>
                    <div style="color:rgba(255,255,255,0.65);font-size:0.88rem;line-height:1.9;">
                        1️⃣ Share this QR code or link<br>
                        2️⃣ Recipient scans QR with their phone<br>
                        3️⃣ Browser opens → file downloads<br>
                        4️⃣ File auto-deletes after expiry<br>
                        <br>
                        <span style="color:rgba(255,255,255,0.35);font-size:0.78rem;">
                            🔒 Secure · No account needed · Free
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("⚠️ Install qrcode for QR generation: pip install qrcode[pil]")
            st.markdown(f"**📋 Direct Link:** `{link}`")

        # Copy link button area
        st.code(link, language=None)
        st.caption("💡 Copy and share this link with anyone to give them access to your file.")

# ═══════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════

def render_media_tools():
    """Main render function — called from app.py."""
    st.markdown(_MT_CSS, unsafe_allow_html=True)

    # Hero
    st.markdown("""
    <div class="mt-hero">
        <div class="mt-hero-title">🎨 Media Tools Suite</div>
        <div class="mt-hero-sub">
            AI Photo Editor · Image→PDF · PDF Converter · File QR Share
            — four powerful tools in one place
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("← Back", key="mt_back"):
        st.session_state.app_mode = "chat"; st.rerun()

    tab1, tab2, tab3, tab4 = st.tabs([
        "🎨 AI Photo Editor",
        "🖼️→📄 Image → PDF",
        "📄→🔀 PDF Converter",
        "🔗 File QR Share",
    ])
    with tab1: _render_photo_editor()
    with tab2: _render_image_to_pdf()
    with tab3: _render_pdf_converter()
    with tab4: _render_file_qr_share()


# ── FREE API ADDITIONS ───────────────────────────────────────────────────────

def get_random_image_url(width: int = 800, height: int = 600, seed: int = None) -> str:
    """Get a free placeholder image URL from Picsum Photos (free, no key)."""
    if seed:
        return f"https://picsum.photos/seed/{seed}/{width}/{height}"
    return f"https://picsum.photos/{width}/{height}"


def get_color_name(hex_color: str) -> dict:
    """Get the name of a color from its hex code (TheColorAPI, free, no key)."""
    import urllib.request, json
    try:
        clean = hex_color.lstrip("#")
        req = urllib.request.Request(
            f"https://www.thecolorapi.com/id?hex={clean}",
            headers={"User-Agent": "ExamHelp/1.0"}
        )
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read().decode())
        return {"name": data.get("name", {}).get("value", ""),
                "hex": data.get("hex", {}).get("value", ""),
                "rgb": data.get("rgb", {}).get("value", ""),
                "hsl": data.get("hsl", {}).get("value", "")}
    except Exception:
        return {"name": hex_color, "hex": hex_color}


def generate_qr_url(data: str, size: int = 200) -> str:
    """Generate a QR code image URL using QR Server API (free, no key)."""
    import urllib.parse
    return f"https://api.qrserver.com/v1/create-qr-code/?size={size}x{size}&data={urllib.parse.quote(data)}"


def get_image_color_palette(image_url: str) -> list:
    """Extract dominant colors from an online image using ColorTag API (free)."""
    import urllib.request, urllib.parse, json
    try:
        url = f"https://colortagit.com/api/extract?img={urllib.parse.quote(image_url)}"
        req = urllib.request.Request(url, headers={"User-Agent": "ExamHelp/1.0"})
        with urllib.request.urlopen(req, timeout=6) as r:
            data = json.loads(r.read().decode())
        return data.get("colors", [])[:5]
    except Exception:
        return []


def shorten_url(long_url: str) -> str:
    """Shorten a URL using is.gd API (free, no key, for file share links)."""
    import urllib.request, urllib.parse
    try:
        api_url = f"https://is.gd/create.php?format=simple&url={urllib.parse.quote(long_url)}"
        req = urllib.request.Request(api_url, headers={"User-Agent": "ExamHelp/1.0"})
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.read().decode().strip()
    except Exception:
        return long_url
