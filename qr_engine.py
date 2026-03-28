"""
qr_engine.py — QR Code Generator + File Sharer Engine
Generates QR codes for URLs, text, vCards, WiFi, and uploaded file data-URIs.
"""
from __future__ import annotations
import io, base64, json
from typing import Optional, Tuple

def _get_qr(data: str, error_correction: str = "H", box_size: int = 10, border: int = 4,
             fill_color: str = "#1a1a2e", back_color: str = "#ffffff") -> Optional[bytes]:
    """Returns PNG bytes of a QR code."""
    try:
        import qrcode
        import qrcode.constants as qrc
        ec_map = {"L": qrc.ERROR_CORRECT_L, "M": qrc.ERROR_CORRECT_M,
                  "Q": qrc.ERROR_CORRECT_Q, "H": qrc.ERROR_CORRECT_H}
        qr = qrcode.QRCode(
            version=None, error_correction=ec_map.get(error_correction, qrc.ERROR_CORRECT_H),
            box_size=box_size, border=border
        )
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color=fill_color, back_color=back_color)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except ImportError:
        return None
    except Exception:
        return None

def generate_text_qr(text: str, **kwargs) -> Optional[bytes]:
    return _get_qr(text, **kwargs)

def generate_url_qr(url: str, **kwargs) -> Optional[bytes]:
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return _get_qr(url, **kwargs)

def generate_vcard_qr(name: str, phone: str = "", email: str = "", org: str = "", url: str = "", **kwargs) -> Optional[bytes]:
    vcard = (
        f"BEGIN:VCARD\nVERSION:3.0\n"
        f"FN:{name}\n"
        f"ORG:{org}\n"
        f"TEL:{phone}\n"
        f"EMAIL:{email}\n"
        f"URL:{url}\n"
        f"END:VCARD"
    )
    return _get_qr(vcard, **kwargs)

def generate_wifi_qr(ssid: str, password: str, security: str = "WPA", hidden: bool = False, **kwargs) -> Optional[bytes]:
    wifi_str = f"WIFI:T:{security};S:{ssid};P:{password};H:{'true' if hidden else 'false'};;"
    return _get_qr(wifi_str, **kwargs)

def generate_email_qr(to: str, subject: str = "", body: str = "", **kwargs) -> Optional[bytes]:
    mailto = f"mailto:{to}"
    parts = []
    if subject: parts.append(f"subject={subject}")
    if body:    parts.append(f"body={body}")
    if parts:   mailto += "?" + "&".join(parts)
    return _get_qr(mailto, **kwargs)

def generate_phone_qr(phone: str, **kwargs) -> Optional[bytes]:
    return _get_qr(f"tel:{phone}", **kwargs)

def generate_sms_qr(phone: str, message: str = "", **kwargs) -> Optional[bytes]:
    sms = f"sms:{phone}"
    if message: sms += f"?body={message}"
    return _get_qr(sms, **kwargs)

def file_to_share_link(file_bytes: bytes, filename: str, mime: str) -> str:
    """Encodes file as base64 data URI for sharing as a download link."""
    b64 = base64.b64encode(file_bytes).decode()
    return f"data:{mime};base64,{b64}"

def generate_file_qr(file_bytes: bytes, filename: str, mime: str = "application/octet-stream",
                     share_url: str = "") -> Tuple[Optional[bytes], str]:
    """
    For small files: encodes as data-URI QR (limited by QR capacity ~3KB).
    For large files: QR encodes the share_url instead.
    Returns (qr_png_bytes, info_message).
    """
    if share_url:
        qr = _get_qr(share_url)
        return qr, f"QR links to: {share_url}"
    
    # Try data-URI approach for very small files
    if len(file_bytes) <= 2048:
        b64 = base64.b64encode(file_bytes).decode()
        data_uri = f"data:{mime};base64,{b64}"
        qr = _get_qr(data_uri)
        if qr:
            return qr, "QR encodes file data directly (scan to open/download)"
    
    # File too large — encode filename + size as info QR
    info = json.dumps({"file": filename, "size": len(file_bytes), "type": mime})
    qr = _get_qr(info)
    return qr, "File too large for direct QR encoding — QR contains file metadata. Use the download button to share."

def qr_to_base64(qr_bytes: bytes) -> str:
    return base64.b64encode(qr_bytes).decode()
