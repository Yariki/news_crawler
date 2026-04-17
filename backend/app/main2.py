
import asyncio
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.scrapers.default import DefaultScraper

BASE_URL =  "https://ria.ru/"
# "https://russian.rt.com/"
# "https://ria.ru/"
# "https://ru.themoscowtimes.com/news"

async def main():
    """A simple test function to demonstrate the DefaultScraper."""
    scraper = DefaultScraper(BASE_URL)

    urs = await scraper.discover_article_urls()

    for u in urs:
        article =  await scraper.fetch_article(u)
        print(f"{article.external_id} {article.title}")
        print("-" * 100)


asyncio.run(main())


