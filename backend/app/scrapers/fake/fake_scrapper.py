
from app.dto.scraped_article import ScrapedArticle
from app.dto.url_feed import UrlFeed
from app.scrapers.base_scraper import BaseScraper
from faker import Faker



class FakeScrapper(BaseScraper):

    def __init__(self):
        super().__init__("")
        self._fake = Faker()


    async def discover_urls(self) -> list[UrlFeed]:
        urls = []

        for i in range(40):
            urls.append(UrlFeed(
                id=self._fake.idi(),
                url=self._fake.url(),
                title=f"Article {i}",
                author=self._fake.name(),
                published=self._fake.date_time(),
                content_html=self._fake.paragraph(),
                content_text=self._fake.paragraph(),
                summary=self._fake.english_text(),
                tags=[],
                checksum=None,
            ))
        return urls


    async def fetch_article(self, feed: UrlFeed) -> ScrapedArticle | None:

        return ScrapedArticle(
            external_id=self._fake.idi(),
            url=feed.url,
            checksum=None,
            title=feed.title,
            author=feed.author,
            content_html=feed.content_html,
            content_text=feed.content_text,
            summary=feed.summary,
            tags=feed.tags,
            language=self._fake.word(),
            published_at=self._fake.date_time(),
            raw_payload_json=self._fake.json_object(),
        )
