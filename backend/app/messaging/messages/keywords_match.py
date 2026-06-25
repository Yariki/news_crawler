from ...messaging.messages.base import BaseMessage, MessageTypes

class KeywordsMatchMessage(BaseMessage):
    """Message class for keywords match events."""
    article_id: str
    matched_keywords: list[str]
    title: str
    url: str
    published_at: str

    def __init__(self, article_id: str, title: str, url: str, matched_keywords: list[str], published_at: str):
        super().__init__(type=MessageTypes.KEYWORDS_MATCH)
        self.article_id = article_id
        self.title = title
        self.url = url
        self.matched_keywords = matched_keywords
        self.published_at = published_at
