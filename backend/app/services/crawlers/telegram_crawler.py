
from datetime import datetime, timezone
import uuid


import httpx
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.status import Status
from app.services.keyword_detector import detect_keywords

from ...scrapers.telegram.telegram_scraper import TelegramScrapper
from ...services.crawlers.base_crawler import BaseCrawler
from ...core.config import settings
from ...models import Source, CrawlJob, Article, KeywordHit
import logging

logger = logging.getLogger(__name__)

class TelegramCrawlerService(BaseCrawler):
    """TelegramCrawler is responsible for orchestrating the crawling process for a specific Telegram channel. It uses the TelegramScrapper to fetch messages, detects keywords, and stores relevant articles in the database."""
    
    def __init__(self, db: AsyncSession, notification_hub):
        """Initializes the TelegramCrawler with a database session and a NotificationHub instance."""
        super().__init__(db, notification_hub)
    
    async def crawl(self, source_id: str, use_delay: bool = True) -> CrawlJob:
        """Executes the crawling process for a given Telegram source. This includes fetching messages from the Telegram channel, detecting keywords, and storing relevant articles in the database."""
        source = await self.db.get(Source, source_id)
        if not source:
            raise ValueError("Source not found")
        
        job = CrawlJob(source_id=source_id, status=Status.RUNNING)
        self.db.add(job)
        await self.db.commit()
        await self.db.refresh(job)
        
        scraper = TelegramScrapper(
            api_id=settings.telegram_api_id,
            api_hash=settings.telegram_api_hash,
            channel=source.base_url,
            last_message_id=source.last_message_id
        )
        created = 0
        try:
            await scraper.start()
            
            scraped_articles, new_last_message_id = await scraper.get_messages()
            job.articles_found = len(scraped_articles)
            
            active_keywords = await self._get_keywords()
            
            for article_data in scraped_articles:
                
                exists = await self.db.scalar(
                    select(Article).where(Article.url == article_data.url)
                )
                if exists:
                    continue
                
                matched_keywords = detect_keywords(article_data.content_text, active_keywords)
                
                article = Article(
                    source_id=source_id,
                    external_id=article_data.external_id,
                    url=article_data.url,
                    title=article_data.title,
                    author=article_data.author,
                    published_at=article_data.published_at,
                    fetched_at=datetime.now(timezone.utc),
                    content_html=article_data.content_html,
                    content_text=article_data.content_text,
                    summary=article_data.summary,
                    language=article_data.language or source.language,
                    tags_csv=(
                        ",".join(article_data.tags) if article_data.tags else None
                    ),
                    raw_payload_json=article_data.raw_payload_json,
                    checksum=article_data.checksum,
                    is_alert=bool(matched_keywords),
                    matched_keywords_csv=(
                        ",".join(matched_keywords) if matched_keywords else None
                    ),
                )
                self.db.add(article)
                await self.db.flush()  # Flush to get the article ID for keyword hits
                if matched_keywords:
                    for keyword in matched_keywords:
                        keyword_hit = KeywordHit(
                            article_id=article.id,
                            keyword=keyword
                        )
                        self.db.add(keyword_hit)
                    await self._send_notification(article, matched_keywords)
                await self._index_article(article, source, matched_keywords)
                
                await self.db.commit()
                await self.db.refresh(article)
                created += 1
                
            
            # Update the last_message_id for incremental scraping
            if new_last_message_id and new_last_message_id != source.last_message_id:
                source.last_message_id = new_last_message_id
                await self.db.commit()
            
            job.status = Status.COMPLETED
            job.articles_created = created
            job.finished_at = datetime.now(timezone.utc)
            
        except httpx.RequestError as ex:
            job.status = Status.FAILED
            job.error_message = f"Network error: {ex}"
            logger.error("Network error crawling source %s: %s", source_id, ex)
        except SQLAlchemyError as ex:
            job.status = Status.FAILED
            job.error_message = f"Database error: {ex}"
            logger.error("Database error crawling source %s: %s", source_id, ex)
        except Exception as ex:
            job.status = Status.FAILED
            job.error_message = f"Unexpected error: {ex}"
            logger.exception("Unexpected error crawling source %s", source_id)
        finally:
            await scraper.stop()
            await self.db.commit()
        
        return job