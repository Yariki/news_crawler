from app.dto import scraped_article


def create_source_payload(name, crawler_key, scrape_interval_minutes, is_enabled):
    return {
        "name": name,
        "base_url": "https://example.com",
        "language": "en",
        "source_type": 1,
        "crawler_key": crawler_key,
        "scrape_interval_minutes": scrape_interval_minutes,
        "is_enabled": is_enabled,
    }
