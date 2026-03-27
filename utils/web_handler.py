import requests
from bs4 import BeautifulSoup
import re


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


def scrape_web_page(url: str, timeout: int = 10) -> tuple[str, str]:
    """
    Scrape readable text content from a web URL.
    Returns (page_text, page_title).
    Raises ValueError with a helpful message on failure.
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=timeout)
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        raise ValueError(f"Could not connect to {url}. Check the URL and your internet connection.")
    except requests.exceptions.Timeout:
        raise ValueError(f"Request to {url} timed out. The site may be slow or unreachable.")
    except requests.exceptions.HTTPError as e:
        raise ValueError(f"HTTP error {e.response.status_code} when accessing {url}.")
    except Exception as e:
        raise ValueError(f"Could not fetch the page: {str(e)}")

    soup = BeautifulSoup(response.text, "html.parser")

    # Remove noisy tags
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "advertisement", "noscript"]):
        tag.decompose()

    # Get page title
    title = soup.title.string.strip() if soup.title and soup.title.string else url

    # Extract main content — prefer <article>, <main>, then fall back to <body>
    main_content = (
        soup.find("article")
        or soup.find("main")
        or soup.find("div", {"id": re.compile(r"content|main|article", re.I)})
        or soup.find("div", {"class": re.compile(r"content|main|article|post", re.I)})
        or soup.body
    )

    if not main_content:
        raise ValueError("Could not extract readable content from this page.")

    # Get text and clean it up
    raw_text = main_content.get_text(separator="\n")
    lines = [line.strip() for line in raw_text.splitlines()]
    cleaned_lines = [line for line in lines if len(line) > 30]  # filter out nav cruft
    page_text = "\n".join(cleaned_lines)

    if len(page_text) < 100:
        raise ValueError("Page content is too short or could not be parsed properly.")

    return page_text, title


def format_web_context(page_text: str, title: str, url: str) -> str:
    """
    Format scraped web content for AI context injection.
    """
    return f"Web Page: {title}\nSource URL: {url}\n\n{page_text}"
