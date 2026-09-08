

from app.core.config import NormalizationSettings
from app.utils.normalization.normalization_result import NormalizationResult

import unicodedata

from app.utils.normalization.noramalization import (
    remove_invisible_chars,
    remove_control_chars,
    normalize_whitespace,
    normalize_newlines,
    norm_repeated_punct,
    normalize_dashes,
    find_urls,
    find_mentions,
    find_hashtags,
)


class TextNormalization:

    VERSION = 1
    
    def __init__(self, settings: NormalizationSettings):
        self._settings = settings


    def normalize_text(self, text: str) -> NormalizationResult:
        raw_text = text
        text = self._normalize_unicode_form(text)
        text = remove_invisible_chars(text)
        text = remove_control_chars(text)
        text = normalize_whitespace(text, self._settings.max_blank_lines)
        text = normalize_newlines(text)
        text = norm_repeated_punct(text, self._settings.max_repeated_punctuations)
        text = normalize_dashes(text)

        urls = find_urls(text)
        mentions = find_mentions(text, self._settings.keep_mentiones)
        hashtags = find_hashtags(text, self._settings.keep_hashtags)

        return NormalizationResult(
            raw_text,
            text,
            text.lower(),
            urls,
            hashtags,
            mentions,
            self.VERSION,
        )

    def _normalize_unicode_form(self, text: str) -> str:
        """Normalize the unicode form of the text."""

        return unicodedata.normalize(self._settings.unicode_form, text)
