def create_source_payload():
    return {
        "name": "Test Source",
        "base_url": "https://example.com",
        "language": "en",
        "source_type": 1,
        "crawler_key": "test_crawler",
        "scrape_interval_minutes": 1440,
        "is_enabled": True,
    }
