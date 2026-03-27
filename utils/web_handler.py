"""web_handler.py — Scrape and clean web page content for study context."""

from __future__ import annotations
import requests
from bs4 import BeautifulSoup

MAX_CHARS = 12_000
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def scrape_web_page(url: str) -> tuple[str, str]:
    """
    Scrape the main text content from a URL.

    Returns:
        (page_text, page_title)

    Raises:
        ValueError on network or parsing failure.
    """
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        raise ValueError(f"Could not fetch URL: {e}")

    soup = BeautifulSoup(resp.text, "html.parser")

    # Remove non-content tags
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
        tag.decompose()

    title = soup.title.string.strip() if soup.title else url

    # Prefer article / main content
    main = soup.find("article") or soup.find("main") or soup.find("body")
    text = main.get_text(separator="\n", strip=True) if main else soup.get_text()

    # Collapse blank lines
    lines = [l for l in text.splitlines() if l.strip()]
    cleaned = "\n".join(lines)

    return cleaned[:MAX_CHARS], title


def format_web_context(text: str, title: str, url: str) -> str:
    return f"Web Article: {title}\nSource: {url}\n\n{text}"
