"""
qr_engine.py — QR Code Generator v3.0 (Upgraded)
Supports: URL, Text, vCard, WiFi, Email, Phone, SMS, Calendar Event, UPI
NEW in v3.0:
  - Logo/image embedding in center of QR
  - Gradient color fill (top-to-bottom linear)
  - Rounded / dot module styles (StyledPilImage)
  - Batch QR from CSV → ZIP download
  - QR Decoder (pyzbar)
  - SVG export
  - Download as PNG / SVG / PDF
  - Live preview base64 URI
"""
from __future__ import annotations
import io, base64, json, urllib.parse, zipfile, csv
from typing import Optional, Tuple, List, Dict
from free_apis import get_qr_image as _api_qr


# ── Color presets ─────────────────────────────────────────────────────────────
QR_THEMES = {
    "Deep Space":   {"fill": "#1a1a2e", "back": "#ffffff"},
    "Midnight Blue":{"fill": "#0f172a", "back": "#e0f2fe"},
    "Forest":       {"fill": "#14532d", "back": "#f0fdf4"},
    "Crimson":      {"fill": "#7f1d1d", "back": "#fff1f2"},
    "Purple Haze":  {"fill": "#4c1d95", "back": "#f5f3ff"},
    "Gold & Black": {"fill": "#0a0a0a", "back": "#fbbf24"},
    "Ocean":        {"fill": "#0c4a6e", "back": "#e0f7ff"},
    "Classic":      {"fill": "#000000", "back": "#ffffff"},
    "Neon Green":   {"fill": "#00ffb4", "back": "#020617"},
    "Sunset":       {"fill": "#c2410c", "back": "#fff7ed"},
}

MODULE_STYLES = ["Square", "Rounded", "Dots", "Gapped Square", "Vertical Bars", "Horizontal Bars"]


# ─────────────────────────────────────────────────────────────────────────────
# CORE QR GENERATOR (upgraded with logo, gradient, module style)
# ─────────────────────────────────────────────────────────────────────────────

def _get_qr(
    data: str,
    error_correction: str = "H",
    box_size: int = 10,
    border: int = 4,
    fill_color: str = "#1a1a2e",
    back_color: str = "#ffffff",
    logo_bytes: Optional[bytes] = None,
    gradient_colors: Optional[List[str]] = None,
    module_style: str = "Square",
) -> Optional[bytes]:
    """
    Returns PNG bytes of a QR code.
    - logo_bytes: PNG/JPG bytes to embed in center (requires error_correction='H')
    - gradient_colors: list of 2 hex strings for top→bottom gradient on dark modules
    - module_style: Square | Rounded | Dots | Gapped Square | Vertical Bars | Horizontal Bars
    Priority: local qrcode library → api.qrserver.com fallback.
    """
    try:
        import qrcode
        import qrcode.constants as qrc
        from PIL import Image, ImageDraw, ImageFilter

        ec_map = {
            "L": qrc.ERROR_CORRECT_L, "M": qrc.ERROR_CORRECT_M,
            "Q": qrc.ERROR_CORRECT_Q, "H": qrc.ERROR_CORRECT_H,
        }

        # ── Styled image factory selector ─────────────────────────────────
        styled_available = False
        try:
            from qrcode.image.styledpil import StyledPilImage
            from qrcode.image.styles.moduledrawers import (
                RoundedModuleDrawer, CircleModuleDrawer,
                GappedSquareModuleDrawer, VerticalBarsDrawer, HorizontalBarsDrawer,
            )
            styled_available = True
        except ImportError:
            pass

        style_map = {
            "Rounded": "RoundedModuleDrawer",
            "Dots": "CircleModuleDrawer",
            "Gapped Square": "GappedSquareModuleDrawer",
            "Vertical Bars": "VerticalBarsDrawer",
            "Horizontal Bars": "HorizontalBarsDrawer",
        }

        qr = qrcode.QRCode(
            version=None,
            error_correction=ec_map.get(error_correction, qrc.ERROR_CORRECT_H),
            box_size=box_size,
            border=border,
        )
        qr.add_data(data)
        qr.make(fit=True)

        # ── Generate base image ───────────────────────────────────────────
        if styled_available and module_style in style_map:
            drawer_map = {
                "RoundedModuleDrawer": RoundedModuleDrawer(),
                "CircleModuleDrawer": CircleModuleDrawer(),
                "GappedSquareModuleDrawer": GappedSquareModuleDrawer(),
                "VerticalBarsDrawer": VerticalBarsDrawer(),
                "HorizontalBarsDrawer": HorizontalBarsDrawer(),
            }
            img = qr.make_image(
                image_factory=StyledPilImage,
                module_drawer=drawer_map[style_map[module_style]],
            ).convert("RGBA")
        else:
            img = qr.make_image(fill_color=fill_color, back_color=back_color).convert("RGBA")

        # ── Apply gradient to dark modules ────────────────────────────────
        if gradient_colors and len(gradient_colors) >= 2:
            try:
                img = _apply_gradient(img, gradient_colors[0], gradient_colors[1], back_color)
            except Exception:
                pass

        # ── Embed logo in center ──────────────────────────────────────────
        if logo_bytes and error_correction == "H":
            try:
                img = _embed_logo(img, logo_bytes)
            except Exception:
                pass

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    except ImportError:
        pass
    except Exception:
        pass

    # ── Free API fallback ─────────────────────────────────────────────────────
    fill_hex = fill_color.lstrip("#")[:6]
    back_hex = back_color.lstrip("#")[:6]
    size_px  = max(100, box_size * 25)
    return _api_qr(
        data=data, size=size_px,
        color=fill_hex, bgcolor=back_hex,
        correction=error_correction,
    )


def _apply_gradient(img, color1: str, color2: str, back_color: str):
    """Apply a top→bottom gradient over the dark modules of a QR PIL image."""
    from PIL import Image, ImageDraw
    import colorsys

    def hex_to_rgb(h):
        h = h.lstrip("#")
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

    c1 = hex_to_rgb(color1)
    c2 = hex_to_rgb(color2)
    back_rgb = hex_to_rgb(back_color)

    img_rgb = img.convert("RGB")
    w, h = img_rgb.size
    result = Image.new("RGB", (w, h), back_rgb)
    pixels_in = img_rgb.load()
    pixels_out = result.load()

    for y in range(h):
        t = y / max(1, h - 1)
        grad_r = int(c1[0] + (c2[0] - c1[0]) * t)
        grad_g = int(c1[1] + (c2[1] - c1[1]) * t)
        grad_b = int(c1[2] + (c2[2] - c1[2]) * t)
        for x in range(w):
            px = pixels_in[x, y]
            brightness = (px[0] * 299 + px[1] * 587 + px[2] * 114) // 1000
            if brightness < 128:  # dark module
                pixels_out[x, y] = (grad_r, grad_g, grad_b)
            else:
                pixels_out[x, y] = back_rgb

    return result.convert("RGBA")


def _embed_logo(qr_img, logo_bytes: bytes):
    """Paste logo centered on QR image at max 20% of QR size."""
    from PIL import Image
    logo = Image.open(io.BytesIO(logo_bytes)).convert("RGBA")
    qr_w, qr_h = qr_img.size
    max_logo = int(min(qr_w, qr_h) * 0.20)
    logo.thumbnail((max_logo, max_logo), Image.LANCZOS)
    lw, lh = logo.size
    pos = ((qr_w - lw) // 2, (qr_h - lh) // 2)
    qr_img = qr_img.convert("RGBA")
    qr_img.paste(logo, pos, logo)
    return qr_img


# ─────────────────────────────────────────────────────────────────────────────
# SVG EXPORT
# ─────────────────────────────────────────────────────────────────────────────

def qr_to_svg(data: str) -> Optional[str]:
    """Generate SVG QR code string. Returns SVG string or None on failure."""
    try:
        import qrcode
        import qrcode.image.svg as qrsvg
        factory = qrsvg.SvgImage
        qr = qrcode.make(data, image_factory=factory)
        buf = io.BytesIO()
        qr.save(buf)
        return buf.getvalue().decode("utf-8")
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# QR DECODER
# ─────────────────────────────────────────────────────────────────────────────

def decode_qr(image_bytes: bytes) -> str:
    """
    Decode QR code from image bytes.
    Returns decoded text, or raises ValueError if nothing found.
    Requires: pip install pyzbar pillow
    """
    try:
        from pyzbar.pyzbar import decode as pyzbar_decode
        from PIL import Image
        img = Image.open(io.BytesIO(image_bytes))
        results = pyzbar_decode(img)
        if results:
            return results[0].data.decode("utf-8")
        raise ValueError("No QR code detected in image.")
    except ImportError:
        # Fallback: try zxingcpp if available
        try:
            import zxingcpp
            from PIL import Image
            import numpy as np
            img = Image.open(io.BytesIO(image_bytes))
            result = zxingcpp.read_barcode(np.array(img))
            if result:
                return result.text
        except Exception:
            pass
        raise ValueError("QR decoder not available. Install pyzbar: pip install pyzbar")
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Decode error: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# BATCH QR FROM CSV
# ─────────────────────────────────────────────────────────────────────────────

def batch_generate_qr(csv_bytes: bytes, theme: str = "Classic") -> Optional[bytes]:
    """
    Parse CSV with columns [label, data, type (optional)].
    Generate one QR per row, zip all PNGs, return zip bytes.
    Returns None on failure.
    """
    try:
        content = csv_bytes.decode("utf-8", errors="replace")
        reader = csv.DictReader(io.StringIO(content))
        # Normalize header names
        rows = []
        for row in reader:
            normalized = {k.strip().lower(): v.strip() for k, v in row.items()}
            rows.append(normalized)

        if not rows:
            return None

        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for i, row in enumerate(rows):
                label = row.get("label", row.get("name", f"qr_{i+1}"))
                data  = row.get("data", row.get("url", row.get("text", "")))
                if not data:
                    continue
                qr_type = row.get("type", "text").lower()
                if qr_type in ("url", "link") and not data.startswith(("http://", "https://")):
                    data = "https://" + data

                qr_bytes = _get_qr(data, fill_color=QR_THEMES.get(theme, QR_THEMES["Classic"])["fill"],
                                   back_color=QR_THEMES.get(theme, QR_THEMES["Classic"])["back"])
                if qr_bytes:
                    clean_label = "".join(c for c in label if c.isalnum() or c in "-_ ").strip()
                    zf.writestr(f"{clean_label or i+1}.png", qr_bytes)

        return zip_buf.getvalue()
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# PDF EXPORT (single QR)
# ─────────────────────────────────────────────────────────────────────────────

def qr_to_pdf(qr_bytes: bytes, title: str = "QR Code") -> Optional[bytes]:
    """Embed QR PNG into a simple PDF. Returns PDF bytes or None."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas as rl_canvas
        from reportlab.lib.units import cm

        buf = io.BytesIO()
        c = rl_canvas.Canvas(buf, pagesize=A4)
        w, h = A4

        c.setFont("Helvetica-Bold", 18)
        c.drawCentredString(w / 2, h - 3 * cm, title)

        img_buf = io.BytesIO(qr_bytes)
        c.drawImage(img_buf, (w - 10 * cm) / 2, (h - 14 * cm) / 2,
                    width=10 * cm, height=10 * cm)
        c.save()
        return buf.getvalue()
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# ORIGINAL GENERATOR FUNCTIONS (all upgraded to pass new options)
# ─────────────────────────────────────────────────────────────────────────────

def generate_text_qr(text: str, theme: str = "Classic",
                     logo_bytes=None, gradient_colors=None, module_style="Square", **kwargs) -> Optional[bytes]:
    t = QR_THEMES.get(theme, QR_THEMES["Classic"])
    return _get_qr(text, fill_color=t["fill"], back_color=t["back"],
                   logo_bytes=logo_bytes, gradient_colors=gradient_colors,
                   module_style=module_style, **kwargs)


def generate_url_qr(url: str, theme: str = "Deep Space",
                    logo_bytes=None, gradient_colors=None, module_style="Square", **kwargs) -> Optional[bytes]:
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    t = QR_THEMES.get(theme, QR_THEMES["Deep Space"])
    return _get_qr(url, fill_color=t["fill"], back_color=t["back"],
                   logo_bytes=logo_bytes, gradient_colors=gradient_colors,
                   module_style=module_style, **kwargs)


def generate_vcard_qr(
    name: str, phone: str = "", email: str = "", org: str = "",
    url: str = "", title: str = "", address: str = "",
    theme: str = "Classic", logo_bytes=None, gradient_colors=None, module_style="Square", **kwargs
) -> Optional[bytes]:
    vcard = (
        f"BEGIN:VCARD\nVERSION:3.0\n"
        f"FN:{name}\nORG:{org}\nTITLE:{title}\n"
        f"TEL:{phone}\nEMAIL:{email}\nURL:{url}\nADR:{address}\n"
        f"END:VCARD"
    )
    t = QR_THEMES.get(theme, QR_THEMES["Classic"])
    return _get_qr(vcard, fill_color=t["fill"], back_color=t["back"],
                   logo_bytes=logo_bytes, gradient_colors=gradient_colors,
                   module_style=module_style, **kwargs)


def generate_wifi_qr(
    ssid: str, password: str, security: str = "WPA", hidden: bool = False,
    theme: str = "Ocean", logo_bytes=None, gradient_colors=None, module_style="Square", **kwargs
) -> Optional[bytes]:
    wifi_str = f"WIFI:T:{security};S:{ssid};P:{password};H:{'true' if hidden else 'false'};;"
    t = QR_THEMES.get(theme, QR_THEMES["Ocean"])
    return _get_qr(wifi_str, fill_color=t["fill"], back_color=t["back"],
                   logo_bytes=logo_bytes, gradient_colors=gradient_colors,
                   module_style=module_style, **kwargs)


def generate_email_qr(
    to: str, subject: str = "", body: str = "",
    theme: str = "Classic", **kwargs
) -> Optional[bytes]:
    mailto = f"mailto:{to}"
    parts = []
    if subject: parts.append(f"subject={urllib.parse.quote(subject)}")
    if body:    parts.append(f"body={urllib.parse.quote(body)}")
    if parts:   mailto += "?" + "&".join(parts)
    t = QR_THEMES.get(theme, QR_THEMES["Classic"])
    return _get_qr(mailto, fill_color=t["fill"], back_color=t["back"], **kwargs)


def generate_phone_qr(phone: str, theme: str = "Classic", **kwargs) -> Optional[bytes]:
    t = QR_THEMES.get(theme, QR_THEMES["Classic"])
    return _get_qr(f"tel:{phone}", fill_color=t["fill"], back_color=t["back"], **kwargs)


def generate_sms_qr(phone: str, message: str = "", theme: str = "Classic", **kwargs) -> Optional[bytes]:
    sms = f"sms:{phone}"
    if message:
        sms += f"?body={urllib.parse.quote(message)}"
    t = QR_THEMES.get(theme, QR_THEMES["Classic"])
    return _get_qr(sms, fill_color=t["fill"], back_color=t["back"], **kwargs)


def generate_calendar_qr(
    title: str, start: str, end: str = "",
    location: str = "", description: str = "",
    theme: str = "Purple Haze", **kwargs
) -> Optional[bytes]:
    vevent = (
        f"BEGIN:VCALENDAR\nVERSION:2.0\n"
        f"BEGIN:VEVENT\n"
        f"SUMMARY:{title}\nDTSTART:{start}\n"
        f"{'DTEND:' + end + chr(10) if end else ''}"
        f"LOCATION:{location}\nDESCRIPTION:{description}\n"
        f"END:VEVENT\nEND:VCALENDAR"
    )
    t = QR_THEMES.get(theme, QR_THEMES["Purple Haze"])
    return _get_qr(vevent, fill_color=t["fill"], back_color=t["back"], **kwargs)


def generate_upi_qr(
    upi_id: str, name: str = "", amount: str = "",
    note: str = "", theme: str = "Gold & Black", **kwargs
) -> Optional[bytes]:
    upi = f"upi://pay?pa={upi_id}"
    if name:   upi += f"&pn={urllib.parse.quote(name)}"
    if amount: upi += f"&am={amount}&cu=INR"
    if note:   upi += f"&tn={urllib.parse.quote(note)}"
    t = QR_THEMES.get(theme, QR_THEMES["Gold & Black"])
    return _get_qr(upi, fill_color=t["fill"], back_color=t["back"], **kwargs)


def generate_file_qr(
    file_bytes: bytes, filename: str,
    mime: str = "application/octet-stream",
    share_url: str = "",
    theme: str = "Classic",
) -> Tuple[Optional[bytes], str]:
    t = QR_THEMES.get(theme, QR_THEMES["Classic"])
    if share_url:
        qr = _get_qr(share_url, fill_color=t["fill"], back_color=t["back"])
        return qr, f"QR links to: {share_url}"
    if len(file_bytes) <= 2048:
        b64      = base64.b64encode(file_bytes).decode()
        data_uri = f"data:{mime};base64,{b64}"
        qr       = _get_qr(data_uri, fill_color=t["fill"], back_color=t["back"])
        if qr:
            return qr, "QR encodes file data directly (scan to open/download)"
    info = json.dumps({"file": filename, "size": len(file_bytes), "type": mime})
    qr   = _get_qr(info, fill_color=t["fill"], back_color=t["back"])
    return qr, "File too large for direct QR — QR contains file metadata."


# ─────────────────────────────────────────────────────────────────────────────
# UTILITY HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def qr_to_base64(qr_bytes: bytes) -> str:
    return base64.b64encode(qr_bytes).decode()


def qr_to_data_uri(qr_bytes: bytes) -> str:
    return f"data:image/png;base64,{qr_to_base64(qr_bytes)}"


def file_to_share_link(file_bytes: bytes, filename: str, mime: str) -> str:
    b64 = base64.b64encode(file_bytes).decode()
    return f"data:{mime};base64,{b64}"


def estimate_qr_capacity(data: str, error_correction: str = "H") -> Dict[str, int]:
    capacities = {"L": 4296, "M": 3391, "Q": 2420, "H": 1852}
    max_chars = capacities.get(error_correction, 1852)
    used = len(data)
    return {
        "used":  used,
        "max":   max_chars,
        "pct":   min(100, round((used / max_chars) * 100, 1)),
        "fits":  used <= max_chars,
    }
