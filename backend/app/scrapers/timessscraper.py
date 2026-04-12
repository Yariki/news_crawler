from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup
from dateutil import parser as date_parser


ARTICLE_LINK_RE = re.compile(r"/\d{4}/\d{2}/\d{2}/.+-a\d+$")
DATE_RE = re.compile(r"\b\d{2}\.\d{2}\.\d{4}\b")


@dataclass
class ScrapedArticle:
    external_id: str
    url: str
    title: str
    author: str | None
    published_at: datetime | None
    content_html: str | None
    content_text: str
    summary: str | None
    language: str
    tags: list[str]
    raw_payload_json: dict
    checksum: str


class TimesScraper:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/") + "/"
        self.client = httpx.Client(
            timeout=30.0,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (compatible; NewsMonitorBot/0.1)"},
        )

    def discover_article_urls(self) -> list[str]:
        response = self.client.get(self.base_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")

        found: list[str] = []
        seen: set[str] = set()
        for anchor in soup.select("a[href]"):
            href = anchor.get("href", "").strip()
            if not href:
                continue
            full_url = urljoin(self.base_url, href)
            path = urlparse(full_url).path.rstrip("/")
            if ARTICLE_LINK_RE.search(path) and full_url not in seen:
                seen.add(full_url)
                found.append(full_url)
        return found

    def scrape_article(self, url: str) -> ScrapedArticle:
        response = self.client.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")

        title = self._get_title(soup)
        published_at = self._get_published_at(soup)
        author = self._get_author(soup)
        content_html, content_text = self._get_content(soup)
        summary = self._build_summary(content_text)
        tags = self._get_tags(soup)
        external_id = self._extract_external_id(url)
        checksum = hashlib.sha256(content_text.encode("utf-8")).hexdigest()

        return ScrapedArticle(
            external_id=external_id,
            url=url,
            title=title,
            author=author,
            published_at=published_at,
            content_html=content_html,
            content_text=content_text,
            summary=summary,
            language="ru",
            tags=tags,
            raw_payload_json={
                "scraped_at": datetime.now(timezone.utc).isoformat(),
                "url": url,
                "title": title,
                "author": author,
                "published_at": published_at.isoformat() if published_at else None,
                "tags": tags,
            },
            checksum=checksum,
        )

    def _get_title(self, soup: BeautifulSoup) -> str:
        for selector in ["h1", "meta[property='og:title']", "title"]:
            if selector.startswith("meta"):
                node = soup.select_one(selector)
                if node and node.get("content"):
                    return node["content"].strip()
            else:
                node = soup.select_one(selector)
                if node and node.get_text(strip=True):
                    return node.get_text(strip=True)
        return "Untitled"

    def _get_published_at(self, soup: BeautifulSoup) -> datetime | None:
        time_node = soup.select_one("time[datetime]")
        if time_node and time_node.get("datetime"):
            try:
                return date_parser.parse(time_node["datetime"])
            except Exception:
                pass

        text = soup.get_text(" ", strip=True)
        match = DATE_RE.search(text)
        if match:
            try:
                return date_parser.parse(match.group(0), dayfirst=True)
            except Exception:
                return None
        return None

    def _get_author(self, soup: BeautifulSoup) -> str | None:
        author_meta = soup.select_one("meta[name='author']")
        if author_meta and author_meta.get("content"):
            return author_meta["content"].strip()
        return None

    def _get_content(self, soup: BeautifulSoup) -> tuple[str | None, str]:
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

    def _build_summary(self, text: str) -> str | None:
        compact = " ".join(text.split())
        return compact[:300] + ("..." if len(compact) > 300 else "") if compact else None

    def _get_tags(self, soup: BeautifulSoup) -> list[str]:
        tags: list[str] = []
        for anchor in soup.select("a[href]"):
            label = anchor.get_text(" ", strip=True)
            if label and len(label) < 60 and label.lower() not in {"подписаться", "читать еще"}:
                href = anchor.get("href", "")
                if "/tag" in href or "/section" in href:
                    tags.append(label)
        return list(dict.fromkeys(tags))[:10]

    def _extract_external_id(self, url: str) -> str:
        match = re.search(r"-a(\d+)$", url.rstrip("/"))
        return match.group(1) if match else url.rstrip("/").split("/")[-1]
