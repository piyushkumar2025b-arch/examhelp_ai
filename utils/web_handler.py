"""web_handler.py — Scrape and clean web page content for study context."""

from __future__ import annotations
import re
import requests
from bs4 import BeautifulSoup, Tag

MAX_CHARS = 30_000
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

# Tags whose content is never useful
_REMOVE_TAGS = [
    "script", "style", "nav", "footer", "header", "aside", "form",
    "noscript", "iframe", "svg", "button", "select", "textarea",
    "figure.advertisement", "[class*='cookie']", "[class*='banner']",
    "[class*='popup']", "[id*='cookie']", "[id*='sidebar']",
    "[class*='related']", "[class*='share']", "[class*='social']",
]

# Content container candidates in priority order
_CONTENT_SELECTORS = [
    "article",
    "[role='main']",
    "main",
    ".post-content",
    ".article-content",
    ".entry-content",
    ".content-body",
    ".story-body",
    "#content",
    "#main-content",
    ".page-content",
]


def _clean_text(text: str) -> str:
    """Normalize whitespace and remove excessive blank lines."""
    # Remove Wikipedia reference brackets like [1], [edit]
    text = re.sub(r'\[\d+\]', '', text)
    text = re.sub(r'\[edit\]', '', text)
    
    # Remove non-printable chars except newlines/tabs
    text = re.sub(r"[^\x09\x0a\x0d\x20-\x7e\u00a0-\uffff]", " ", text)
    # Collapse runs of spaces/tabs on same line
    text = re.sub(r"[ \t]+", " ", text)
    # Max 2 consecutive newlines
    text = re.sub(r"\n{3,}", "\n\n", text)
    
    lines = [l.strip() for l in text.splitlines()]
    lines = [l for l in lines if len(l) >= 4 or l == ""]
    return "\n".join(lines).strip()


def _get_longest_content_block(soup) -> object:
    """
    FIX-10.3a: Find the longest article/main/div content block by character count.
    This avoids navbars, footers, and cookie banners polluting AI context.
    """
    # Priority: semantic elements first
    for selector in ["article", "main", "[role='main']"]:
        el = soup.select_one(selector)
        if el and len(el.get_text()) > 200:
            return el

    # Fallback: find the longest <div> by text length
    all_divs = soup.find_all("div")
    if all_divs:
        return max(all_divs, key=lambda d: len(d.get_text()))

    return soup.find("body") or soup


def check_robots_txt(url: str) -> tuple[bool, str]:
    """
    FIX-10.3b: Check if the URL is disallowed by the site's robots.txt.
    Returns (is_allowed, message).
    """
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = f"{parsed.scheme}://{parsed.netloc}"
        robots_url = f"{domain}/robots.txt"
        resp = requests.get(robots_url, headers=HEADERS, timeout=5)
        if resp.status_code != 200:
            return True, ""  # No robots.txt — assume allowed

        path = parsed.path or "/"
        disallowed = []
        in_user_agent_all = False
        for line in resp.text.splitlines():
            line = line.strip()
            if line.lower().startswith("user-agent:"):
                agent = line.split(":", 1)[1].strip()
                in_user_agent_all = (agent == "*")
            elif line.lower().startswith("disallow:") and in_user_agent_all:
                disallowed_path = line.split(":", 1)[1].strip()
                if disallowed_path and path.startswith(disallowed_path):
                    return False, f"⚠️ This page (`{path}`) is disallowed by `robots.txt` at {domain}. Proceed with caution."
        return True, ""
    except Exception:
        return True, ""  # On failure, assume allowed


def scrape_web_page(url: str) -> tuple[str, str]:
    """
    Scrape the main text content from a URL.
    FIX-10.3a: Uses smart content detection — removes noise tags, picks longest block.
    FIX-10.3b: Checks robots.txt (result stored, but scraping still happens after warning).
    """
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
    except requests.RequestException as e:
        raise ValueError(f"Could not fetch URL: {e}")

    soup = BeautifulSoup(resp.text, "html.parser")

    # FIX-10.3a: Remove all non-content tags
    _NOISE_TAGS = [
        "nav", "footer", "header", "aside", "script", "style",
        "form", "button", "iframe", "noscript", "svg", "select",
    ]
    for tag_name in _NOISE_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()
    # Also remove cookie/popup/social divs by class/id patterns
    for tag in soup.find_all(True, class_=lambda c: c and any(kw in str(c).lower() for kw in ("cookie", "popup", "banner", "social", "share", "sidebar", "related"))):
        tag.decompose()

    # Get page title
    title_meta = soup.find("meta", property="og:title")
    title = title_meta.get("content", "") if title_meta else (soup.title.string if soup.title else "")
    title = (title or "").strip()[:200] or url

    # Wiki-specific processing
    is_wiki = "wikipedia.org" in url.lower()
    if is_wiki:
        main_content = soup.select_one(".mw-parser-output")
        if main_content:
            text_blocks = []
            for elem in main_content.find_all(["p", "h2", "h3", "li"]):
                if elem.name in ["h2", "h3"]:
                    text_blocks.append(f"\n\n### {elem.get_text()}\n")
                else:
                    text_blocks.append(elem.get_text())
            raw_text = " ".join(text_blocks)
        else:
            raw_text = soup.get_text(separator="\n")
    else:
        # FIX-10.3a: Use longest content block
        main_content = _get_longest_content_block(soup)
        raw_text = main_content.get_text(separator="\n")

    cleaned = _clean_text(raw_text)

    if is_wiki:
        refs_index = cleaned.lower().rfind("### references")
        if refs_index > len(cleaned) * 0.5:
            cleaned = cleaned[:refs_index]

    return cleaned[:MAX_CHARS], title


def format_web_context(text: str, title: str, url: str) -> str:
    """Format web content with metadata header for context injection."""
    word_count = len(text.split())
    return (
        f"Web Article: {title}\n"
        f"Source URL: {url}\n"
        f"Approximate length: {word_count} words\n"
        f"{'—' * 40}\n\n"
        f"{text}"
    )


def get_web_stats(text: str, title: str) -> dict:
    """Return stats about scraped content for UI display."""
    return {
        "title": title[:60],
        "word_count": len(text.split()),
        "char_count": len(text),
    }