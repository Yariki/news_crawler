from __future__ import annotations

from app.scrapers.base_scraper import BaseScraper



class DefaultScraper(BaseScraper):
    """A default scraper implementation that can be used as a fallback for sources without a custom scraper."""
    pass