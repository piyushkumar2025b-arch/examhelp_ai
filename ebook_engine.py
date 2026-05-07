"""
ebook_engine.py — Free E-Book & Audiobook Engine (no keys required)
Sources: Project Gutenberg · Open Library · LibriVox · Standard Ebooks
"""
import requests, re, io
from typing import List, Dict, Optional

TIMEOUT = 12
GUT_API  = "https://gutendex.com"
OL_API   = "https://openlibrary.org"
LV_API   = "https://librivox.org/api"
SE_API   = "https://standardebooks.org"


# ─────────────────────────────────────────────────────────────────────────────
# Project Gutenberg (via Gutendex API — free, no key)
# ─────────────────────────────────────────────────────────────────────────────

def search_gutenberg(query: str, page: int = 1) -> Dict:
    """
    Search Gutenberg books via Gutendex.
    Returns {"results": [...], "count": int, "next": bool}
    Each result: {id, title, authors, cover, subjects, languages, download_txt, download_epub, download_html}
    """
    try:
        r = requests.get(f"{GUT_API}/books",
                         params={"search": query, "page": page},
                         timeout=TIMEOUT)
        if r.status_code != 200:
            return {"results": [], "count": 0, "next": False}
        data = r.json()
        results = []
        for b in data.get("results", []):
            formats = b.get("formats", {})
            cover = formats.get("image/jpeg", "")
            results.append({
                "id":            b["id"],
                "title":         b.get("title", ""),
                "authors":       ", ".join(a["name"] for a in b.get("authors", [])),
                "cover":         cover,
                "subjects":      b.get("subjects", [])[:4],
                "languages":     b.get("languages", []),
                "download_count": b.get("download_count", 0),
                "download_txt":  formats.get("text/plain; charset=us-ascii", "")
                                 or formats.get("text/plain; charset=utf-8", ""),
                "download_epub": formats.get("application/epub+zip", ""),
                "download_html": formats.get("text/html; charset=utf-8", "")
                                 or formats.get("text/html", ""),
                "source":        "Gutenberg",
            })
        return {"results": results, "count": data.get("count", 0),
                "next": bool(data.get("next"))}
    except Exception:
        return {"results": [], "count": 0, "next": False}


def get_gutenberg_text(book_id: int) -> Optional[str]:
    """Download plain-text content for a Gutenberg book by ID."""
    try:
        # Get formats first
        r = requests.get(f"{GUT_API}/books/{book_id}", timeout=TIMEOUT)
        if r.status_code != 200:
            return None
        formats = r.json().get("formats", {})
        txt_url = (formats.get("text/plain; charset=us-ascii")
                   or formats.get("text/plain; charset=utf-8")
                   or formats.get("text/plain"))
        if not txt_url:
            return None
        r2 = requests.get(txt_url, timeout=30)
        if r2.status_code == 200:
            return r2.text
        return None
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Open Library (free, no key)
# ─────────────────────────────────────────────────────────────────────────────

def search_open_library(query: str, limit: int = 15) -> List[Dict]:
    """
    Search Open Library. Returns list of book dicts.
    Each: {title, authors, cover_url, ol_key, subjects, year, read_url}
    """
    try:
        r = requests.get(f"{OL_API}/search.json",
                         params={"q": query, "limit": limit, "fields": "key,title,author_name,cover_i,subject,first_publish_year,ia,has_fulltext"},
                         timeout=TIMEOUT)
        if r.status_code != 200:
            return []
        docs = r.json().get("docs", [])
        results = []
        for d in docs:
            cover_id = d.get("cover_i")
            cover = f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg" if cover_id else ""
            ia = d.get("ia", [])
            read_url = f"https://archive.org/details/{ia[0]}" if ia else ""
            results.append({
                "title":    d.get("title",""),
                "authors":  ", ".join(d.get("author_name",[])[:3]),
                "cover":    cover,
                "ol_key":   d.get("key",""),
                "subjects": d.get("subject",[])[:4],
                "year":     d.get("first_publish_year",""),
                "read_url": read_url,
                "has_full": bool(d.get("has_fulltext")),
                "source":   "Open Library",
            })
        return results
    except Exception:
        return []


# ─────────────────────────────────────────────────────────────────────────────
# LibriVox (free audiobooks, no key)
# ─────────────────────────────────────────────────────────────────────────────

def search_librivox(query: str, limit: int = 12) -> List[Dict]:
    """
    Search LibriVox audiobooks via their free API.
    Returns list of {id, title, authors, cover, url_librivox, url_iarchive, sections_count, language}
    """
    try:
        r = requests.get(
            f"{LV_API}/feed/audiobooks",
            params={"title": query, "format": "json", "limit": limit},
            timeout=TIMEOUT,
        )
        if r.status_code != 200:
            # Try author search
            r = requests.get(f"{LV_API}/feed/audiobooks",
                             params={"author": query, "format": "json", "limit": limit},
                             timeout=TIMEOUT)
        if r.status_code != 200:
            return []
        books = r.json().get("books", [])
        results = []
        for b in books:
            if isinstance(b, dict):
                authors = ", ".join(
                    f"{a.get('first_name','')} {a.get('last_name','')}".strip()
                    for a in b.get("authors", [])
                )
                results.append({
                    "id":       b.get("id",""),
                    "title":    b.get("title",""),
                    "authors":  authors,
                    "cover":    b.get("url_zip_file","").replace(".zip","_128kb.m4b") or "",
                    "url_librivox": b.get("url_librivox",""),
                    "url_rss":  b.get("url_rss",""),
                    "language": b.get("language",""),
                    "sections": b.get("num_sections","0"),
                    "description": re.sub(r'<[^>]+>','', b.get("description",""))[:200],
                    "source":   "LibriVox",
                })
        return results
    except Exception:
        return []


def get_librivox_chapters(book_id: str) -> List[Dict]:
    """
    Get all audio chapters for a LibriVox book.
    Returns list of {title, listen_url, duration, reader}
    """
    try:
        r = requests.get(
            f"{LV_API}/feed/audiosections",
            params={"book_id": book_id, "format": "json"},
            timeout=TIMEOUT,
        )
        if r.status_code != 200:
            return []
        sections = r.json().get("sections", [])
        chapters = []
        for s in sections:
            if isinstance(s, dict):
                chapters.append({
                    "title":      s.get("section_number","") + ". " + s.get("title",""),
                    "listen_url": s.get("listen_url",""),
                    "duration":   s.get("playtime",""),
                    "reader":     f"{s.get('reader_id','')}" ,
                })
        return chapters
    except Exception:
        return []


# ─────────────────────────────────────────────────────────────────────────────
# Standard Ebooks (beautifully formatted, no key)
# ─────────────────────────────────────────────────────────────────────────────

def search_standard_ebooks(query: str) -> List[Dict]:
    """
    Search Standard Ebooks via their OPDS catalog (XML/Atom).
    Returns list of {title, authors, cover, epub_url, description}
    """
    try:
        r = requests.get(
            "https://standardebooks.org/opds/all",
            headers={"Accept": "application/atom+xml"},
            timeout=TIMEOUT,
        )
        if r.status_code != 200:
            return []
        xml = r.text
        q_lower = query.lower()
        # Extract entries that match query
        entries = re.findall(r'<entry>(.*?)</entry>', xml, re.S)
        results = []
        for entry in entries:
            title = re.search(r'<title[^>]*>([^<]+)</title>', entry)
            author = re.search(r'<name>([^<]+)</name>', entry)
            summary = re.search(r'<summary[^>]*>(.*?)</summary>', entry, re.S)
            cover = re.search(r'href="([^"]+\.jpg)"', entry)
            epub = re.search(r'href="([^"]+\.epub)"', entry)
            t = title.group(1) if title else ""
            a = author.group(1) if author else ""
            if q_lower in t.lower() or q_lower in a.lower():
                results.append({
                    "title":    t,
                    "authors":  a,
                    "cover":    cover.group(1) if cover else "",
                    "epub_url": epub.group(1) if epub else "",
                    "description": re.sub(r'<[^>]+>','',summary.group(1) if summary else "")[:200],
                    "source":   "Standard Ebooks",
                })
            if len(results) >= 10:
                break
        return results
    except Exception:
        return []
