import unittest
from app.utils.normalization.text_normalization import TextNormalization
from app.core.config import NormalizationSettings


class TestTextNormalizer(unittest.TestCase):
    def setUp(self):
        self._norm = TextNormalization(settings=NormalizationSettings())

    # ---------- Whitespace -------------------------------------------------
    def test_whitespace_collapse(self):
        txt = "Hello     world"
        res = self._norm.normalize_text(txt)
        self.assertEqual(res.normalization_text, "Hello world")

    # ---------- Newlines ---------------------------------------------------
    def test_paragraph_newlines(self):
        txt = "Paragraph 1\n\n\n\nParagraph 2"
        res = self._norm.normalize_text(txt)
        self.assertEqual(res.normalization_text, "Paragraph 1\n\nParagraph 2")

    # ---------- Unicode whitespace -----------------------------------------
    def test_unicode_nbsp(self):
        txt = "Kyiv\u00A0Ukraine"
        res = self._norm.normalize_text(txt)
        self.assertEqual(res.normalization_text, "Kyiv Ukraine")

    # ---------- Zero‑width characters ---------------------------------------
    def test_zero_width(self):
        txt = "Ky\u200Biv"
        res = self._norm.normalize_text(txt)
        self.assertEqual(res.normalization_text, "Kyiv")

    # ---------- Telegram mention --------------------------------------------
    def test_mention_extraction(self):
        txt = "Source: @example_channel"
        res = self._norm.normalize_text(txt)
        self.assertIn("example_channel", res.mentions)

    # ---------- Hashtag extraction -------------------------------------------
    def test_hashtag_extraction(self):
        txt = "News from #Kyiv"
        res = self._norm.normalize_text(txt)
        self.assertIn("Kyiv", res.hashtags)

    # ---------- URL tracking‑param stripping --------------------------------
    def test_url_cleaning(self):
        txt = "https://example.com/news?id=42&utm_source=telegram"
        res = self._norm.normalize_text(txt)
        self.assertEqual(res.urls, ["https://example.com/news?id=42&utm_source=telegram"])

    # ---------- Cyrillic preservation ---------------------------------------
    def test_cyrillic_preservation(self):
        txt = "Київ Москва Україна Россия"
        res = self._norm.normalize_text(txt)
        self.assertEqual(res.normalization_text, txt)

    # ---------- Idempotency ------------------------------------------------
    def test_idempotent(self):
        txt = "Hello   world!!\n\n\nParagraph"
        first = self._norm.normalize_text(txt)
        second = self._norm.normalize_text(first.normalization_text)
        self.assertEqual(first.normalization_text, second.normalization_text)

if __name__ == "__main__":
    unittest.main()