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
    # Remove non-printable chars except newlines/tabs
    text = re.sub(r"[^\x09\x0a\x0d\x20-\x7e\u00a0-\uffff]", " ", text)
    # Collapse runs of spaces/tabs on same line
    text = re.sub(r"[ \t]+", " ", text)
    # Max 2 consecutive newlines
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Strip lines that are too short to be content (< 4 chars)
    lines = [l.strip() for l in text.splitlines()]
    lines = [l for l in lines if len(l) >= 4 or l == ""]
    return "\n".join(lines).strip()


def scrape_web_page(url: str) -> tuple[str, str]:
    """
    Scrape the main text content from a URL.
    Uses smart content detection to extract the article/main text.

    Returns:
        (page_text, page_title)

    Raises:
        ValueError on network or parsing failure.
    """
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
    except requests.RequestException as e:
        raise ValueError(f"Could not fetch URL: {e}")

    soup = BeautifulSoup(resp.text, "html.parser")

    # Remove non-content elements
    for selector in _REMOVE_TAGS:
        try:
            for tag in soup.select(selector):
                tag.decompose()
        except Exception:
            pass
    for tag in soup(["script", "style"]):
        tag.decompose()

    # Get page title
    title = ""
    if soup.find("meta", property="og:title"):
        title = soup.find("meta", property="og:title").get("content", "")
    if not title and soup.title:
        title = soup.title.string or ""
    title = title.strip()[:200] or url

    # Get meta description for context
    description = ""
    meta_desc = soup.find("meta", attrs={"name": "description"})
    if meta_desc:
        description = meta_desc.get("content", "").strip()[:300]

    # Try content selectors in priority order
    main_content: Tag | None = None
    for selector in _CONTENT_SELECTORS:
        found = soup.select_one(selector)
        if found:
            content_text = found.get_text()
            if len(content_text.split()) > 100:  # Must have real content
                main_content = found
                break

    # Fall back to body
    if not main_content:
        main_content = soup.find("body") or soup

    # Extract and clean text
    raw_text = main_content.get_text(separator="\n")
    cleaned = _clean_text(raw_text)

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