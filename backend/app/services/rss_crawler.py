import asyncio
from datetime import datetime, timezone

import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CrawlJob, Source, Article, KeywordHit
from app.models.status import Status
from app.scrapers.rss.rss_scraper import RssScraper
from app.services.base_crawler import BaseCrawler
from app.services.es import elastic_service
from app.services.keyword_detector import detect_keywords
from app.services.notifications import notification_hub


class RssCrawler(BaseCrawler):


    def __init__(self, db: AsyncSession):
        super().__init__(db)

    async def crawl(self, source_id: int) -> CrawlJob:
        """"""
        source = await self.db.execute(Source, source_id)
        if not source:
            raise ValueError("Source not found")

        job = CrawlJob(source_id=source_id, status=Status.RUNNING)
        self.db.add(job)
        await self.db.commit()
        await self.db.refresh(job)

        try:
            scraper = RssScraper(source.url)
            urls = await asyncio.to_thread(scraper.discover_rss_urls)
            job.articles_found = len(urls)
            active_keywords = await self.get_keywords()
            created = 0

            for url in urls:
                exists = await self.db.scalar(select(Article).where(Article.url == url))
                if exists:
                    continue

                article_data = await asyncio.to_thread(scraper.fetch_article, url)
                if not article_data:
                    continue

                matched_words = detect_keywords(article_data.content_text, active_keywords)
                article = Article(
                    source_id=source_id,
                    external_id=article_data.id,
                    url=article.url,
                    title=article_data.title,
                    author=article_data.author,
                    published_at=article_data.published_at,
                    content_html=article_data.content_html,
                    content_text=article_data.content_text,
                    summary=article_data.summary,
                    language=article_data.language,
                    tags_csv=",".join(article_data.tags_csv) if article_data.tags_csv else None,
                    raw_payload_json=article_data.raw_payload_json,
                    checksum=article_data.checksum,
                    is_alert=bool(matched_words),
                    matched_keywords_csv=",".join(matched_words) if matched_words else None,
                )

                self.db.add(article)
                await self.db.flush()

                for keyword in matched_words:
                    self.db.add(KeywordHit(article_id=article.id, keyword=keyword.strip()))

                await self.db.commit()
                await self.db.refresh(article)

                await elastic_service.index_article(
                    {
                        "article_id": article.id,
                        "source_id": source_id,
                        "source_name": source.name,
                        "title": article.title,
                        "content_text": article.content_text,
                        "published_at": article.published_at.isoformat() if article.published_at else None,
                        "url": article.url,
                        "language": article.language,
                        "is_alert": article.is_alert,
                        "matched_keywords": matched_words,
                    }
                )

                created += 1
                if matched_words:
                    await notification_hub.broadcast(
                        "keywords_alert", {
                            "article_id": article.id,
                            "title": article.title,
                            "url": article.url,
                            "matched_keywords": matched_words,
                            "published_at": article.published_at,
                        }
                    )

                job.articles_created = created
                job.status = Status.COMPLETED
                job.finished_at = datetime.now(timezone.utc)
                await self.db.commit()
                await self.db.refresh(job)

                return job

        except Exception as ex:
            job.status = Status.FAILED
            job.error_message = str(ex)
        finally:
            job.finished_at = datetime.now()
            await self.db.commit()
            await self.db.refresh(job)