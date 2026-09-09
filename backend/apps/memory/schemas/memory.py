from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

MemoryScope = Literal["personal", "workspace"]
MemoryType = Literal["preference", "business_rule", "confirmed_example"]


def _normalize_list(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        cleaned = value.strip()
        key = cleaned.casefold()
        if cleaned and key not in seen:
            result.append(cleaned)
            seen.add(key)
    return result


def _current_time_for(value: datetime) -> datetime:
    """Return a comparable current time for naive or timezone-aware values."""
    return datetime.now(tz=value.tzinfo) if value.tzinfo is not None else datetime.now()


class MemoryCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=2, max_length=4000)
    memory_type: MemoryType = "preference"
    scope: MemoryScope = "personal"
    keywords: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    datasource_id: Optional[int] = None
    expires_at: Optional[datetime] = None
    priority: int = Field(default=0, ge=-10, le=10)

    @field_validator("title", "content")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("keywords", "dependencies")
    @classmethod
    def normalize_lists(cls, value: list[str]) -> list[str]:
        return _normalize_list(value)

    @model_validator(mode="after")
    def validate_expiry(self):
        if self.expires_at and self.expires_at <= _current_time_for(self.expires_at):
            raise ValueError("expires_at must be in the future")
        return self


class MemoryUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    content: Optional[str] = Field(default=None, min_length=2, max_length=4000)
    memory_type: Optional[MemoryType] = None
    keywords: Optional[list[str]] = None
    dependencies: Optional[list[str]] = None
    datasource_id: Optional[int] = None
    expires_at: Optional[datetime] = None
    priority: Optional[int] = Field(default=None, ge=-10, le=10)

    @field_validator("title", "content")
    @classmethod
    def strip_optional_text(cls, value: Optional[str]) -> Optional[str]:
        return value.strip() if value is not None else value

    @field_validator("keywords", "dependencies")
    @classmethod
    def normalize_optional_lists(cls, value: Optional[list[str]]) -> Optional[list[str]]:
        return _normalize_list(value) if value is not None else value

    @model_validator(mode="after")
    def validate_expiry(self):
        if self.expires_at and self.expires_at <= _current_time_for(self.expires_at):
            raise ValueError("expires_at must be in the future")
        return self


class MemoryStatusUpdate(BaseModel):
    status: Literal["active", "paused"]
