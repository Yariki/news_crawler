import asyncio
from datetime import timezone, datetime

from app.models import Source, Article
from app.models.status import Status
from app.repositories.crawljob_repository import CrawlJobRepository
from app.services.crawlers.base_crawler import BaseCrawler
from app.services.keyword_detector import detect_keywords


class FakeCrawlerService(BaseCrawler):

    def __init__(self, db, rabbitmq_client):
        super().__init__(db, rabbitmq_client)

    async def crawl(self, source_id:str, use_delay: bool = True):
        """Crawl method for the FakeCrawler. This method is responsible for orchestrating the crawling process for a specific source. It uses the FakeScrapper to fetch articles, detects keywords, and stores relevant articles in the database."""
        created = 0
        
        source = await self._db.get(Source, source_id)
        if not source:
            raise ValueError("Source not found")

        crawl_rp = CrawlJobRepository(self._db)
        job = await crawl_rp.create_crawl_job(source_id, Status.RUNNING)
        await self._send_job_update(job, articles_found=0, articles_created=0)
        
        try:
            active_keywords = await self._get_keywords()
            
            from app.scrapers.fake.fake_scrapper import FakeScrapper
            scraper = FakeScrapper(active_keywords=active_keywords)
            urls = await scraper.discover_urls()

            job.articles_found = len(urls)
            await self._update_job_info(crawl_rp, job, created)
            

            for url_feed in urls:
                fetched_article = await scraper.fetch_article(url_feed)

                matched_keywords = detect_keywords(fetched_article.content_text, active_keywords)

                article = Article(
                    source_id=source_id,
                    external_id=fetched_article.external_id,
                    url=fetched_article.url,
                    title=fetched_article.title,
                    author=fetched_article.author,
                    published_at=fetched_article.published_at,
                    fetched_at=datetime.now(timezone.utc).isoformat(),
                    content_html=fetched_article.content_html,
                    content_text=fetched_article.content_text,
                    summary=fetched_article.summary,
                    language=fetched_article.language or source.language,
                    tags_csv=(
                        ",".join(fetched_article.tags) if fetched_article.tags else None
                    ),
                    raw_payload_json=fetched_article.raw_payload_json,
                    checksum=fetched_article.checksum,
                    is_alert=bool(matched_keywords),
                    matched_keywords_csv=(
                        ",".join(matched_keywords) if matched_keywords else None
                    ),
                )

                if matched_keywords:
                    await self._send_matched_words_notification(article, matched_keywords)

                created += 1

                await self._update_job_info(crawl_rp, job, created)

                if use_delay:
                    await asyncio.sleep(1)

            job.status = Status.COMPLETED
            job.articles_created = created
            job.finished_at = datetime.now(timezone.utc)
        except Exception  as e:
            job.status = Status.FAILED
            await self._send_job_update(job, articles_found=job.articles_found, articles_created=created)
            raise e
        finally:
            await self._db.commit()
            await self._send_job_update(job, articles_found=job.articles_found, articles_created=created)

        return job




