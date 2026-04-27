"""media_tools_addon.py — Step 34: Batch image converter + metadata editor + background remover"""
import streamlit as st, io, zipfile
from PIL import Image

def render_media_tools_addon():
    ma1, ma2, ma3 = st.tabs(["📦 Batch Converter", "🏷️ Image Metadata", "✂️ Background Remover"])

    with ma1:
        st.markdown("**📦 Batch Image Converter**")
        imgs = st.file_uploader("Upload images (multiple):", type=["png","jpg","jpeg","webp","bmp"],
                                 accept_multiple_files=True, key="mta_batch_imgs")
        out_fmt = st.selectbox("Convert all to:", ["PNG","JPG","WEBP","BMP"], key="mta_out_fmt")
        quality = st.slider("Quality (JPG/WEBP):", 50, 100, 85, key="mta_quality")
        resize_toggle = st.checkbox("Resize all images?", key="mta_resize_tog")
        if resize_toggle:
            rc1, rc2 = st.columns(2)
            new_w = rc1.number_input("Width px:", min_value=50, max_value=8000, value=800, key="mta_new_w")
            new_h = rc2.number_input("Height px:", min_value=50, max_value=8000, value=600, key="mta_new_h")

        if imgs and st.button("📦 Convert All", type="primary", use_container_width=True, key="mta_batch_btn"):
            zip_buf = io.BytesIO()
            prog = st.progress(0)
            with zipfile.ZipFile(zip_buf, "w") as zf:
                for i, f in enumerate(imgs):
                    prog.progress(int(i/len(imgs)*100))
                    try:
                        img = Image.open(f).convert("RGB")
                        if resize_toggle: img = img.resize((int(new_w), int(new_h)), Image.LANCZOS)
                        buf = io.BytesIO()
                        fmt = "JPEG" if out_fmt == "JPG" else out_fmt
                        kw = {"quality": quality} if fmt in ("JPEG","WEBP") else {}
                        img.save(buf, format=fmt, **kw)
                        new_name = f.name.rsplit(".",1)[0] + f".{out_fmt.lower()}"
                        zf.writestr(new_name, buf.getvalue())
                    except Exception as e:
                        zf.writestr(f"{f.name}_error.txt", str(e))
            prog.progress(100)
            zip_buf.seek(0)
            st.success(f"✅ Converted {len(imgs)} images!")
            st.download_button("⬇️ Download ZIP", zip_buf.getvalue(), f"converted_{out_fmt.lower()}.zip", key="mta_batch_dl")

    with ma2:
        st.markdown("**🏷️ Image Metadata Viewer & Editor**")
        meta_img = st.file_uploader("Upload image:", type=["png","jpg","jpeg","webp"], key="mta_meta_img")
        if meta_img:
            img = Image.open(meta_img)
            st.image(img, width=300)
            # Basic metadata
            meta = {
                "Format": img.format or meta_img.type,
                "Size": f"{img.width} × {img.height} px",
                "Mode": img.mode,
                "File size": f"{meta_img.size/1024:.1f} KB",
            }
            # EXIF if available
            try:
                exif_data = img._getexif()
                if exif_data:
                    from PIL.ExifTags import TAGS
                    for tag_id, value in list(exif_data.items())[:10]:
                        tag = TAGS.get(tag_id, tag_id)
                        if isinstance(value, (str, int, float)):
                            meta[f"EXIF: {tag}"] = str(value)[:60]
            except Exception: pass

            st.markdown("**📋 Metadata:**")
            for k,v in meta.items():
                st.markdown(f"• **{k}**: `{v}`")

            # Strip metadata option
            st.markdown("---")
            if st.button("🧹 Strip All Metadata (Privacy)", key="mta_strip", use_container_width=True):
                clean = Image.new(img.mode, img.size)
                clean.putdata(list(img.getdata()))
                buf = io.BytesIO()
                clean.save(buf, format="PNG")
                st.success("✅ Metadata stripped!")
                st.download_button("⬇️ Download Clean Image", buf.getvalue(), "clean_image.png", key="mta_clean_dl")

    with ma3:
        st.markdown("**✂️ Background Remover**")
        st.markdown("""
        <div style="background:rgba(99,102,241,0.07);border:1px solid rgba(99,102,241,0.2);
            border-radius:12px;padding:12px 16px;margin-bottom:14px;font-size:0.84rem;color:rgba(255,255,255,0.6);">
        🤖 Uses AI to remove image backgrounds. Install rembg for best results: <code>pip install rembg</code>
        </div>""", unsafe_allow_html=True)
        bg_img = st.file_uploader("Upload image:", type=["png","jpg","jpeg","webp"], key="mta_bg_img")
        if bg_img:
            st.image(bg_img, caption="Original", width=300)
            if st.button("✂️ Remove Background", type="primary", use_container_width=True, key="mta_bg_btn"):
                with st.spinner("Removing background..."):
                    try:
                        from rembg import remove
                        img_bytes = bg_img.read()
                        result_bytes = remove(img_bytes)
                        result_img = Image.open(io.BytesIO(result_bytes))
                        st.image(result_img, caption="Background Removed", width=300)
                        buf = io.BytesIO(); result_img.save(buf, format="PNG"); buf.seek(0)
                        st.download_button("⬇️ Download PNG (transparent)", buf.getvalue(), "no_background.png", key="mta_bg_dl")
                    except ImportError:
                        st.error("rembg not installed. Run: pip install rembg")
                    except Exception as e:
                        # Fallback: simple color threshold removal
                        st.warning(f"AI removal failed ({e}). Trying simple threshold method...")
                        try:
                            import numpy as np
                            bg_img.seek(0); img = Image.open(bg_img).convert("RGBA")
                            data = np.array(img)
                            # Simple: make white/near-white pixels transparent
                            r,g,b,a = data[:,:,0],data[:,:,1],data[:,:,2],data[:,:,3]
                            mask = (r>200) & (g>200) & (b>200)
                            data[mask,3] = 0
                            result = Image.fromarray(data)
                            st.image(result, caption="Background Removed (threshold)", width=300)
                            buf = io.BytesIO(); result.save(buf,format="PNG"); buf.seek(0)
                            st.download_button("⬇️ Download", buf.getvalue(), "no_bg.png", key="mta_bg_dl2")
                        except Exception as e2:
                            st.error(str(e2))
