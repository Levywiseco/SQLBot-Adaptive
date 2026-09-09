from datetime import datetime
from typing import Any, Optional

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    Identity,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class FeedbackEvent(SQLModel, table=True):
    """Immutable user feedback bound to the exact answer that was reviewed."""

    __tablename__ = "feedback_event"
    __table_args__ = (
        UniqueConstraint("oid", "user_id", "idempotency_key", name="uq_feedback_idempotency"),
    )

    id: Optional[int] = Field(
        default=None,
        sa_column=Column(BigInteger, Identity(always=True), primary_key=True),
    )
    oid: int = Field(sa_column=Column(BigInteger, nullable=False, index=True))
    user_id: int = Field(sa_column=Column(BigInteger, nullable=False, index=True))
    chat_record_id: int = Field(
        sa_column=Column(
            BigInteger,
            ForeignKey("chat_record.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    feedback_type: str = Field(max_length=64, nullable=False, index=True)
    correction_text: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    memory_title: Optional[str] = Field(default=None, max_length=255)
    memory_content: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    memory_keywords: list[str] = Field(
        default_factory=list,
        sa_column=Column(JSONB, nullable=False, default=list),
    )
    idempotency_key: str = Field(max_length=128, nullable=False)
    answer_snapshot: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSONB, nullable=False, default=dict),
    )
    status: str = Field(default="recorded", max_length=32, nullable=False)
    created_at: datetime = Field(
        default_factory=datetime.now,
        sa_column=Column(DateTime(timezone=False), nullable=False),
    )
    processed_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=False), nullable=True),
    )
