import hashlib

from telethon import TelegramClient
from telethon.tl.custom.message import Message

from app.dto.scraped_article import ScrapedArticle

SESSION_NAME = "telegram_scraper_session"

class TelegramScrapper:
    """TelegramScrapper is responsible for connecting to the Telegram API, retrieving messages from a specified channel, and processing them for keyword detection and storage in the database."""
    
    def __init__ (self, api_id: str, api_hash: str, channel: str, last_message_id: str | None = None):
        self._api_id = api_id
        self._api_hash = api_hash
        self._channel = channel
        self._channel_username = self._channel.lstrip("@")
        self._client = TelegramClient(SESSION_NAME, int(api_id), api_hash)
        self._last_message_id = last_message_id # This will be used to track the last processed message ID for incremental scraping
        self._entity = None
        
        
    async def start(self):
        """Starts the Telegram client and retrieves the channel entity for scraping."""
        await self._client.connect()
        # Scheduler jobs must be non-interactive: fail fast if authorization was not done beforehand.
        if not await self._client.is_user_authorized():
            raise RuntimeError(
                "Telegram session is not authorized. Run scripts/telegram_authorize.py once in an interactive terminal."
            )
        self._entity = await self._client.get_entity(self._channel_username)
    
    async def stop(self):
        """Stops the Telegram client."""
        await self._client.disconnect()
        
    async def get_messages(self) -> tuple[list[ScrapedArticle], str | None]:
        """Fetches messages from the specified Telegram channel and processes them into ScrapedArticle objects."""
        if self._entity is None:
            await self.start()
        
        messages = None
        if self._last_message_id:
            messages = await self._client.get_messages(self._entity, min_id=int(self._last_message_id))
        else:
            messages = await self._client.get_messages(self._entity, limit=100)  # Fetch the latest 100 messages if no last_message_id is provided  
        
        scraped_articles = []
        new_last_message_id = self._last_message_id
        if messages:
            for message in messages:
                article = self._message_to_article(message)
                if article:
                    scraped_articles.append(article)
            new_last_message_id = str(max((m.id for m in messages)))
        
        return scraped_articles, new_last_message_id
            
    def _message_to_article(self, message: Message) -> ScrapedArticle | None:
        text = message.message or ""
        if not text.strip():
            return None

        title = self._build_title(text)
        url = f"https://t.me/{self._channel_username}/{message.id}"
        checksum = hashlib.sha256(text.encode("utf-8")).hexdigest()

        return ScrapedArticle(
            external_id=str(message.id),
            url=url,
            title=title,
            author=self._channel_username,
            published_at=message.date,
            content_html=None,
            content_text=text,
            summary=self._build_summary(text),
            language=None,
            tags=[],
            raw_payload_json={
                "message_id": message.id,
                "channel_username": self._channel_username,
                "views": getattr(message, "views", None),
                "forwards": getattr(message, "forwards", None),
                "has_media": message.media is not None,
            },
            checksum=checksum,
        )

    def _build_title(self, text: str) -> str:
        first_line = next((line.strip() for line in text.splitlines() if line.strip()), "")
        if not first_line:
            return "Telegram message"
        return first_line[:120]

    def _build_summary(self, text: str) -> str | None:
        compact = " ".join(text.split())
        if not compact:
            return None
        return compact[:300] + ("..." if len(compact) > 300 else "")