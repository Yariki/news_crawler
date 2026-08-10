from operator import is_
from typing import Any, Awaitable, Callable

import pytest

from app.models import User
from app.schemas.source import SourceCreateUpdate


@pytest.fixture(name="create_source")
def create_source(faker) -> Callable[[Any], Awaitable[SourceCreateUpdate]]:

    def _create_source_payload(**kwargs: dict[Any, Any]) -> dict[str, Any]:
        source =  SourceCreateUpdate(
            name=kwargs.get("name", faker.company()),
            base_url=kwargs.get("base_url", faker.url()),
            language=kwargs.get("language", "en"),
            source_type=kwargs.get("source_type", 1),
            crawler_key=kwargs.get("crawler_key", faker.word()),
            scrape_interval_minutes=kwargs.get("scrape_interval_minutes", 60),
            is_enabled=kwargs.get("is_enabled", True)
        )

        return source.model_copy(update=kwargs)

    return _create_source_payload