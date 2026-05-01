from bs4 import BeautifulSoup

ARTICLE_CHARACTERS_NUMBER = 40

def extract_rss_content_html(item: dict) -> str | None:
    """Extract rich HTML body from RSS/Atom entry if available."""
    content_blocks = item.get("content") or []
    for block in content_blocks:
        value = block.get("value")
        if value and len(value.strip()) > ARTICLE_CHARACTERS_NUMBER:
            return value

    summary = item.get("summary")
    if summary and len(summary.strip()) > ARTICLE_CHARACTERS_NUMBER:
        return summary

    return None

def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text(" ", strip=True)
    return " ".join(text.split())

def get_content(soup: BeautifulSoup) -> tuple[str | None, str]:
    for container_selector in ["article", "main", "body"]:
        container = soup.select_one(container_selector)
        if not container:
            continue

        paragraphs = [p.get_text(" ", strip=True) for p in container.select("p")]
        paragraphs = [p for p in paragraphs if len(p) > 40]

        if paragraphs:
            html = "\n".join(str(p) for p in container.select("p"))
            text = "\n\n".join(paragraphs)
            return html, text

    return None, soup.get_text(" ", strip=True)