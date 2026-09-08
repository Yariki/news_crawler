
from dataclasses import dataclass, field


@dataclass
class NormalizationResult:

    raw_text: str

    normalization_text: str
    normalization_text_lower: str

    urls: list[str] =  field(default_factory=list)
    hashtags: list[str] = field(default_factory=list)
    mentions: list[str] = field(default_factory=list)

    normalization_version: int = field(default=1)

    def __init__(
        self,
        raw_text: str,
        normalization_text: str,
        normalization_text_lower: str,
        urls: list[str] | None = None,
        hashtags: list[str] | None = None,
        mentions: list[str] | None = None,
        normalization_version: int = 1,
    ) -> None:
        self.raw_text = raw_text
        self.normalization_text = normalization_text
        self.normalization_text_lower = normalization_text_lower
        self.urls = [] if urls is None else urls
        self.hashtags = [] if hashtags is None else hashtags
        self.mentions = [] if mentions is None else mentions
        self.normalization_version = normalization_version
