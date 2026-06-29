from pydantic import Field
from app.models.source_type import SourceType


from pydantic import BaseModel, HttpUrl, UUID4


class SourceCreateUpdate(BaseModel):
    name: str = Field(min_length=1)
    base_url: HttpUrl
    language: str
    source_type: int = Field(gt=0, le=SourceType.RSS.value)
    crawler_key: str
    scrape_interval_minutes: int = Field(gt=0, default=1440)
    is_enabled: bool = True


class SourceRead(BaseModel):
    id: UUID4
    name: str
    base_url: str
    language: str
    source_type: int
    crawler_key: str
    is_enabled: bool
    scrape_interval_minutes: int

    model_config = {"from_attributes": True}


class SourceRunResponse(BaseModel):
    id: str
    status: str = "ok"  # "ok" | "error"
    message: str
