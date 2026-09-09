from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

FeedbackType = Literal[
    "correct",
    "result_wrong",
    "metric_wrong",
    "remember_preference",
    "save_example",
]


class FeedbackCreate(BaseModel):
    chat_record_id: int
    feedback_type: FeedbackType
    correction_text: Optional[str] = Field(default=None, max_length=4000)
    memory_title: Optional[str] = Field(default=None, max_length=255)
    memory_content: Optional[str] = Field(default=None, max_length=4000)
    memory_keywords: list[str] = Field(default_factory=list)
    idempotency_key: str = Field(min_length=8, max_length=128)

    @field_validator("correction_text", "memory_title", "memory_content")
    @classmethod
    def strip_optional_text(cls, value: Optional[str]) -> Optional[str]:
        return value.strip() if value is not None else value

    @field_validator("memory_keywords")
    @classmethod
    def normalize_keywords(cls, value: list[str]) -> list[str]:
        return list(dict.fromkeys(item.strip() for item in value if item.strip()))

    @model_validator(mode="after")
    def validate_details(self):
        if self.feedback_type in {"result_wrong", "metric_wrong", "save_example"}:
            if not self.correction_text or len(self.correction_text) < 3:
                raise ValueError("correction_text with at least 3 characters is required")
        if self.feedback_type == "remember_preference":
            if not self.memory_content or len(self.memory_content) < 2:
                raise ValueError("memory_content is required when remembering a preference")
        return self
