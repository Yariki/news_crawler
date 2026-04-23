from __future__ import annotations

from pydantic import UUID4, BaseModel, Field


class MonitoredKeywordRead(BaseModel):
    id: UUID4
    keyword: str
    is_enabled: bool

    model_config = {"from_attributes": True}


class MonitoredKeywordCreate(BaseModel):
    keyword: str = Field(min_length=1, max_length=128)

class MonitoredKeywordUpdate(BaseModel): 
    is_enabled: bool
    keyword: str = Field(min_length=1, max_length=128) 
