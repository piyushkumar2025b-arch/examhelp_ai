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


def scrape_web_page(url: str) -> tuple[str, str]:
    """
    Scrape the main text content from a URL.
    Uses smart content detection, with specialized hooks for Wikipedia and similar Wikis.
    """
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
    except requests.RequestException as e:
        raise ValueError(f"Could not fetch URL: {e}")

    soup = BeautifulSoup(resp.text, "html.parser")

    # Remove non-content elements
    for selector in _REMOVE_TAGS:
        for tag in soup.select(selector):
            tag.decompose()
    for tag in soup(["script", "style"]):
        tag.decompose()

    # Get page title
    title = soup.find("meta", property="og:title")
    title = title.get("content", "") if title else (soup.title.string if soup.title else "")
    title = title.strip()[:200] or url

    # Wiki Specific Processing
    is_wiki = "wikipedia.org" in url.lower()
    
    if is_wiki:
        # For Wikipedia, target the precise content div
        main_content = soup.select_one(".mw-parser-output")
        if main_content:
            text_blocks = []
            for elem in main_content.find_all(['p', 'h2', 'h3', 'li']):
                if elem.name in ['h2', 'h3']:
                    text_blocks.append(f"\n\n### {elem.get_text()}\n")
                else:
                    text_blocks.append(elem.get_text())
            raw_text = " ".join(text_blocks)
        else:
            raw_text = soup.get_text(separator="\n")
    else:
        # Standard processing
        main_content: Tag | None = None
        for selector in _CONTENT_SELECTORS:
            found = soup.select_one(selector)
            if found and len(found.get_text().split()) > 100:
                main_content = found
                break
        
        if not main_content:
            main_content = soup.find("body") or soup
        raw_text = main_content.get_text(separator="\n")

    cleaned = _clean_text(raw_text)
    
    # Wikipedia often has a massive references section that wastes tokens
    if is_wiki:
        refs_index = cleaned.lower().rfind("### references")
        if refs_index > len(cleaned) * 0.5: # only slice if references are at the bottom half
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