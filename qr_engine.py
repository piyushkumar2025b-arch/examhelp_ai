"""
qr_engine.py — QR Code Generator v2.0
Supports: URL, Text, vCard, WiFi, Email, Phone, SMS, Calendar Event, UPI
- Primary: qrcode library (local, full color control)
- Fallback: api.qrserver.com (free, no key, no library needed)
"""
from __future__ import annotations
import io, base64, json, urllib.parse
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
}


def _get_qr(
    data: str,
    error_correction: str = "H",
    box_size: int = 10,
    border: int = 4,
    fill_color: str = "#1a1a2e",
    back_color: str = "#ffffff",
) -> Optional[bytes]:
    """Returns PNG bytes of a QR code.
    Priority: qrcode library (local) → api.qrserver.com (free API, no key).
    """
    # ── 1. Try local qrcode library (full color support) ─────────────────
    try:
        import qrcode
        import qrcode.constants as qrc
        ec_map = {
            "L": qrc.ERROR_CORRECT_L, "M": qrc.ERROR_CORRECT_M,
            "Q": qrc.ERROR_CORRECT_Q, "H": qrc.ERROR_CORRECT_H,
        }
        qr  = qrcode.QRCode(
            version=None,
            error_correction=ec_map.get(error_correction, qrc.ERROR_CORRECT_H),
            box_size=box_size, border=border,
        )
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color=fill_color, back_color=back_color)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except ImportError:
        pass  # library not installed — try free API
    except Exception:
        pass

    # ── 2. Free API fallback (api.qrserver.com, no key) ──────────────────
    fill_hex  = fill_color.lstrip("#")[:6]
    back_hex  = back_color.lstrip("#")[:6]
    size_px   = max(100, box_size * 25)
    return _api_qr(
        data        = data,
        size        = size_px,
        color       = fill_hex,
        bgcolor     = back_hex,
        correction  = error_correction,
    )


def generate_text_qr(text: str, theme: str = "Classic", **kwargs) -> Optional[bytes]:
    t = QR_THEMES.get(theme, QR_THEMES["Classic"])
    return _get_qr(text, fill_color=t["fill"], back_color=t["back"], **kwargs)


def generate_url_qr(url: str, theme: str = "Deep Space", **kwargs) -> Optional[bytes]:
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    t = QR_THEMES.get(theme, QR_THEMES["Deep Space"])
    return _get_qr(url, fill_color=t["fill"], back_color=t["back"], **kwargs)


def generate_vcard_qr(
    name: str, phone: str = "", email: str = "", org: str = "",
    url: str = "", title: str = "", address: str = "",
    theme: str = "Classic", **kwargs
) -> Optional[bytes]:
    vcard = (
        f"BEGIN:VCARD\nVERSION:3.0\n"
        f"FN:{name}\n"
        f"ORG:{org}\n"
        f"TITLE:{title}\n"
        f"TEL:{phone}\n"
        f"EMAIL:{email}\n"
        f"URL:{url}\n"
        f"ADR:{address}\n"
        f"END:VCARD"
    )
    t = QR_THEMES.get(theme, QR_THEMES["Classic"])
    return _get_qr(vcard, fill_color=t["fill"], back_color=t["back"], **kwargs)


def generate_wifi_qr(
    ssid: str, password: str,
    security: str = "WPA", hidden: bool = False,
    theme: str = "Ocean", **kwargs
) -> Optional[bytes]:
    wifi_str = f"WIFI:T:{security};S:{ssid};P:{password};H:{'true' if hidden else 'false'};;"
    t = QR_THEMES.get(theme, QR_THEMES["Ocean"])
    return _get_qr(wifi_str, fill_color=t["fill"], back_color=t["back"], **kwargs)


def generate_email_qr(
    to: str, subject: str = "", body: str = "",
    theme: str = "Classic", **kwargs
) -> Optional[bytes]:
    mailto = f"mailto:{to}"
    parts  = []
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
    """Generate a calendar event QR (VCALENDAR format)."""
    vevent = (
        f"BEGIN:VCALENDAR\nVERSION:2.0\n"
        f"BEGIN:VEVENT\n"
        f"SUMMARY:{title}\n"
        f"DTSTART:{start}\n"
        f"{'DTEND:' + end + chr(10) if end else ''}"
        f"LOCATION:{location}\n"
        f"DESCRIPTION:{description}\n"
        f"END:VEVENT\n"
        f"END:VCALENDAR"
    )
    t = QR_THEMES.get(theme, QR_THEMES["Purple Haze"])
    return _get_qr(vevent, fill_color=t["fill"], back_color=t["back"], **kwargs)


def generate_upi_qr(
    upi_id: str, name: str = "", amount: str = "",
    note: str = "", theme: str = "Gold & Black", **kwargs
) -> Optional[bytes]:
    """Generate a UPI payment QR code."""
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
    """Generate QR for a file — encode URL if given, else metadata."""
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


def qr_to_base64(qr_bytes: bytes) -> str:
    """Convert QR PNG bytes to base64 string for HTML embedding."""
    return base64.b64encode(qr_bytes).decode()


def qr_to_data_uri(qr_bytes: bytes) -> str:
    """Convert QR PNG bytes to data URI."""
    return f"data:image/png;base64,{qr_to_base64(qr_bytes)}"


def file_to_share_link(file_bytes: bytes, filename: str, mime: str) -> str:
    b64 = base64.b64encode(file_bytes).decode()
    return f"data:{mime};base64,{b64}"


def estimate_qr_capacity(data: str, error_correction: str = "H") -> Dict[str, int]:
    """Estimate how full the QR code will be (useful for large data)."""
    # Rough capacities for version 40 QR at various EC levels
    capacities = {"L": 4296, "M": 3391, "Q": 2420, "H": 1852}
    max_chars   = capacities.get(error_correction, 1852)
    used        = len(data)
    return {
        "used":       used,
        "max":        max_chars,
        "pct":        min(100, round((used / max_chars) * 100, 1)),
        "fits":       used <= max_chars,
    }
