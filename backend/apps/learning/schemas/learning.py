from pydantic import BaseModel, Field, field_validator


class CandidateReview(BaseModel):
    review_note: str = Field(min_length=3, max_length=2000)

    @field_validator("review_note")
    @classmethod
    def strip_note(cls, value: str) -> str:
        return value.strip()
