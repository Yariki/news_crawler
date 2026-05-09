import asyncio
import sys
from pathlib import Path

from app.db.session import AsyncSessionLocal
from app.dto.rss_feed import RssFeed
from app.dto.scraped_article import ScrapedArticle
from app.scrapers.rss.rss_scraper import RssScraper
from app.services.crawlers.html_crawler import HtmlCrawlService
from app.services.crawlers.rss_crawler import RssCrawlService

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.scrapers.default import DefaultScraper

BASE_URL = "https://ria.ru/"
# "https://russian.rt.com/"
# "https://ria.ru/"
# "https://ru.themoscowtimes.com/news"


# async def main():
#     """A simple test function to demonstrate the DefaultScraper."""
#     scraper = DefaultScraper(BASE_URL)
#
#     urs = await scraper.discover_article_urls()
#
#     for u in urs:
#         article = await scraper.fetch_article(u)
#         print(f"{article.external_id} {article.title}")
#         print("-" * 100)
#
#
# asyncio.run(main())

# rss_url = "http://newsrss.bbc.co.uk/rss/newsonline_world_edition/front_page/rss.xml"
# rss_url2= "http://www.nytimes.com/services/xml/rss/nyt/World.xml"
# rss_url3 = "http://texty.org.ua/mod/news/?view=rss"
#
# async def main_rss_read():
#     scraper = RssScraper(rss_url3)
#
#     feeds = await scraper.discover_rss_urls()
#     for feed in feeds:
#         article: ScrapedArticle = await scraper.fetch_article(feed)
#         if article:
#             print(f"{article.external_id} {article.title}")
#             print("-" * 100)
#
# asyncio.run(main_rss_read())


async def mail_crawl():
    source_id = "a2bc2d89-65a9-4b37-9780-517dda5bb8f0"

    async with AsyncSessionLocal() as db:
        service = HtmlCrawlService(db)
        await service.crawl(source_id)


if __name__ == "__main__":
    asyncio.run(mail_crawl())
