import asyncio
from datetime import timezone, datetime
from uuid import uuid4


from app.models import Source, Article
from app.utils.normalization.text_normalization import TextNormalization
from app.core.config import get_normalization_settings
from app.models.status import Status
from app.repositories.crawljob_repository import CrawlJobRepository
from app.repositories.outbox_repository import OutboxRepository
from app.services.crawlers.base_crawler import BaseCrawler
from app.services.keyword_detector import detect_keywords


class FakeCrawlerService(BaseCrawler):

    def __init__(self, db, permission_granted, rabbitmq_client):
        super().__init__(db, permission_granted, rabbitmq_client)

    async def crawl(self, source_id:str, use_delay: bool = True):
        """Crawl method for the FakeCrawler. This method is responsible for orchestrating the crawling process for a specific source. It uses the FakeScrapper to fetch articles, detects keywords, and stores relevant articles in the database."""
        created = 0
        
        source = await self._db.get(Source, source_id)
        if not source:
            raise ValueError("Source not found")

        crawl_rp = CrawlJobRepository(self._db, self._permission_granted)
        job = await crawl_rp.create_crawl_job(source_id, Status.RUNNING)
        await self._send_job_update(job, articles_found=0, articles_created=0)
        
        text_normalizer = TextNormalization(settings=get_normalization_settings())
        
        try:
            active_keywords = await self._get_keywords()
            
            from app.scrapers.fake.fake_scrapper import FakeScrapper
            scraper = FakeScrapper(active_keywords=active_keywords)
            urls = await scraper.discover_urls()

            job.articles_found = len(urls)
            await self._update_job_info(crawl_rp, job, created)
            

            for url_feed in urls:
                fetched_article = await scraper.fetch_article(url_feed)

                normalized_text = text_normalizer.normalize_text(fetched_article.content_text)
                matched_keywords = detect_keywords(normalized_text.normalization_text, active_keywords)
                

                article = Article(
                    id = uuid4(),
                    source_id=UUID(source_id),
                    external_id=fetched_article.external_id,
                    url=fetched_article.url,
                    title=fetched_article.title,
                    author=fetched_article.author,
                    published_at=fetched_article.published_at,
                    fetched_at=datetime.now(timezone.utc),
                    content_html=fetched_article.content_html,
                    content_text=fetched_article.content_text,
                    normalized_text=normalized_text.normalization_text,
                    normalized_text_lower=normalized_text.normalization_text_lower,
                    urls=normalized_text.urls,
                    hashtags=normalized_text.hashtags,
                    mentions=normalized_text.mentions,
                    normalization_version=normalized_text.normalization_version,
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
                    owner_id=source.owner_id
                )

                await self._enqueue_outbox_event(source, article, matched_keywords)
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
        finally:
            await self._db.commit()
            await self._send_job_update(job, articles_found=job.articles_found, articles_created=created)

        return job




