
from app.dto.scraped_article import ScrapedArticle
from app.dto.url_feed import UrlFeed
from app.scrapers.base_scraper import BaseScraper
from faker import Faker



class FakeScrapper(BaseScraper):

    def __init__(self, active_keywords: list[str] = None):
        super().__init__("")
        self._fake = Faker()
        self._active_keywords = active_keywords if active_keywords is not None else []
    

    async def discover_urls(self) -> list[UrlFeed]:
        urls = []

        for i in range(40):
            urls.append(UrlFeed(
                id=self._fake.uuid4(),
                url=self._fake.url(),
                title=f"Article {i}",
                author=self._fake.name(),
                published=self._fake.date_time(),
                content_html=self._fake.paragraph(ext_word_list=self._active_keywords),
                content_text=self._fake.paragraph(ext_word_list=self._active_keywords),
                summary=self._fake.text(),
                tags=[],
                checksum=None,
            ))
        return urls


    async def fetch_article(self, feed: UrlFeed) -> ScrapedArticle | None:

        return ScrapedArticle(
            external_id=self._fake.uuid4(),
            url=feed.url,
            checksum=feed.checksum,
            title=feed.title,
            author=feed.author,
            content_html=feed.content_html,
            content_text=feed.content_text,
            summary=feed.summary,
            tags=feed.tags,
            language=self._fake.word(),
            published_at=self._fake.date_time(),
            raw_payload_json={
                    prop: self._fake.word() for prop in ["prop1", "prop2", "prop3"]
                },
        )
