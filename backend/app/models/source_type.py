from enum import IntEnum


class SourceType(IntEnum):
    """Enum representing the type of source."""
    UNKNOWN = 0
    NEWS_SITE = 1
    BLOG = 2
    FORUM = 3
    SOCIAL_MEDIA = 4
    TELEGRAM_CHANNEL = 5
    WHATSAPP_CHANNEL = 6
    OTHER = 7