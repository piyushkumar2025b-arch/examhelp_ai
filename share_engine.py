"""
share_engine.py — Real QR Sharing Engine
Uploads content to free anonymous hosts, shortens URLs, generates scannable QR codes.

Backends (all free, no keys):
  Upload:   0x0.st · file.io · temp.sh
  Shorten:  tinyurl.com API · cleanuri.com · is.gd
  QR:       qr_engine (local) → api.qrserver.com (fallback)
"""
import io, json, base64, requests, time
from typing import Optional, Tuple, Dict

TIMEOUT = 15


# ─────────────────────────────────────────────────────────────────────────────
# FILE UPLOAD (anonymous, free, no key)
# ─────────────────────────────────────────────────────────────────────────────

def upload_to_0x0(data: bytes, filename: str = "file.txt",
                  mime: str = "text/plain") -> Optional[str]:
    """Upload to 0x0.st — free, no account, returns direct URL. Max 512MB."""
    try:
        r = requests.post(
            "https://0x0.st",
            files={"file": (filename, io.BytesIO(data), mime)},
            timeout=TIMEOUT,
        )
        if r.status_code == 200 and r.text.strip().startswith("http"):
            return r.text.strip()
    except Exception:
        pass
    return None


def upload_to_fileio(data: bytes, filename: str = "file.txt",
                     mime: str = "text/plain") -> Optional[str]:
    """Upload to file.io — one-time download link, 14 day expiry."""
    try:
        r = requests.post(
            "https://file.io",
            files={"file": (filename, io.BytesIO(data), mime)},
            data={"expires": "14d"},
            timeout=TIMEOUT,
        )
        if r.status_code in (200, 201):
            j = r.json()
            if j.get("success"):
                return j.get("link", "")
    except Exception:
        pass
    return None


def upload_content(data: bytes, filename: str = "share.txt",
                   mime: str = "text/plain") -> Optional[str]:
    """Try upload backends in order, return first working URL."""
    for fn in [upload_to_0x0, upload_to_fileio]:
        url = fn(data, filename, mime)
        if url:
            return url
    return None


# ─────────────────────────────────────────────────────────────────────────────
# URL SHORTENER (free, no key)
# ─────────────────────────────────────────────────────────────────────────────

def shorten_tinyurl(url: str) -> Optional[str]:
    """TinyURL free API — no key needed."""
    try:
        r = requests.get(
            "https://tinyurl.com/api-create.php",
            params={"url": url},
            timeout=TIMEOUT,
        )
        if r.status_code == 200 and "tinyurl.com" in r.text:
            return r.text.strip()
    except Exception:
        pass
    return None


def shorten_isgd(url: str) -> Optional[str]:
    """is.gd free shortener — no key."""
    try:
        r = requests.get(
            "https://is.gd/create.php",
            params={"format": "simple", "url": url},
            timeout=TIMEOUT,
        )
        if r.status_code == 200 and "is.gd" in r.text:
            return r.text.strip()
    except Exception:
        pass
    return None


def shorten_url(url: str) -> str:
    """Shorten URL with fallback chain. Returns shortest available or original."""
    for fn in [shorten_tinyurl, shorten_isgd]:
        short = fn(url)
        if short:
            return short
    return url  # return original if all shorteners fail


# ─────────────────────────────────────────────────────────────────────────────
# QR GENERATION (wraps qr_engine)
# ─────────────────────────────────────────────────────────────────────────────

def make_share_qr(url: str, theme: str = "Deep Space") -> Optional[bytes]:
    """Generate a QR PNG for a URL using qr_engine with API fallback."""
    try:
        from qr_engine import generate_url_qr
        qr = generate_url_qr(url, theme=theme)
        if qr:
            return qr
    except Exception:
        pass
    # Hard fallback: api.qrserver.com
    try:
        r = requests.get(
            "https://api.qrserver.com/v1/create-qr-code/",
            params={"data": url, "size": "300x300", "format": "png",
                    "color": "1a1a2e", "bgcolor": "ffffff", "ecc": "H"},
            timeout=TIMEOUT,
        )
        if r.status_code == 200:
            return r.content
    except Exception:
        pass
    return None


# ─────────────────────────────────────────────────────────────────────────────
# HIGH-LEVEL SHARE BUILDERS
# ─────────────────────────────────────────────────────────────────────────────

def share_text(text: str, title: str = "Shared Text") -> Dict:
    """
    Upload text, shorten URL, generate QR.
    Returns:
      {"url": str, "short_url": str, "qr_bytes": bytes|None,
       "success": bool, "error": str|None}
    """
    data = f"# {title}\n\n{text}".encode("utf-8")
    raw_url = upload_content(data, filename="share.md", mime="text/markdown")
    if not raw_url:
        return {"success": False, "error": "Upload failed (no internet or host down).",
                "url": "", "short_url": "", "qr_bytes": None}
    short = shorten_url(raw_url)
    qr    = make_share_qr(short)
    return {"success": True, "error": None,
            "url": raw_url, "short_url": short, "qr_bytes": qr}


def share_image(img_bytes: bytes, filename: str = "image.png") -> Dict:
    """Upload image, shorten, QR."""
    raw_url = upload_content(img_bytes, filename=filename, mime="image/png")
    if not raw_url:
        return {"success": False, "error": "Upload failed.",
                "url": "", "short_url": "", "qr_bytes": None}
    short = shorten_url(raw_url)
    qr    = make_share_qr(short)
    return {"success": True, "error": None,
            "url": raw_url, "short_url": short, "qr_bytes": qr}


def share_qr_image(qr_bytes: bytes, label: str = "QR Code") -> Dict:
    """Upload the QR image itself (PNG) and return its shareable URL + meta-QR."""
    raw_url = upload_content(qr_bytes, filename=f"{label}.png", mime="image/png")
    if not raw_url:
        return {"success": False, "error": "Upload failed.",
                "url": "", "short_url": "", "qr_bytes": None}
    short = shorten_url(raw_url)
    meta_qr = make_share_qr(short)   # QR of the URL that shows the QR image
    return {"success": True, "error": None,
            "url": raw_url, "short_url": short, "qr_bytes": meta_qr}


def share_chat(chat_history: list, title: str = "ExamHelp AI Chat") -> Dict:
    """Serialize chat history, upload as JSON, return share result."""
    try:
        minimal = [{"role": m["role"], "content": m["content"]} for m in chat_history]
        text_lines = []
        for m in minimal:
            role = "You" if m["role"] == "user" else "ExamHelp AI"
            text_lines.append(f"**{role}:** {m['content']}")
        full_text = f"# {title}\n\n" + "\n\n---\n\n".join(text_lines)
        data = full_text.encode("utf-8")
    except Exception as e:
        return {"success": False, "error": str(e),
                "url": "", "short_url": "", "qr_bytes": None}

    raw_url = upload_content(data, filename="chat.md", mime="text/markdown")
    if not raw_url:
        return {"success": False, "error": "Upload failed.",
                "url": "", "short_url": "", "qr_bytes": None}
    short = shorten_url(raw_url)
    qr    = make_share_qr(short)
    return {"success": True, "error": None,
            "url": raw_url, "short_url": short, "qr_bytes": qr}


def share_url_direct(url: str) -> Dict:
    """Shorten + QR for any URL directly (no upload needed)."""
    short = shorten_url(url)
    qr    = make_share_qr(short)
    return {"success": True, "error": None,
            "url": url, "short_url": short, "qr_bytes": qr}
