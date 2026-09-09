from datetime import datetime
from typing import Any, Optional

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    Identity,
    Integer,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class LearningCandidate(SQLModel, table=True):
    """A proposed lesson that cannot affect shared answers until reviewed."""

    __tablename__ = "learning_candidate"
    __table_args__ = (
        UniqueConstraint("feedback_event_id", name="uq_learning_candidate_feedback"),
    )

    id: Optional[int] = Field(
        default=None,
        sa_column=Column(BigInteger, Identity(always=True), primary_key=True),
    )
    oid: int = Field(sa_column=Column(BigInteger, nullable=False, index=True))
    feedback_event_id: int = Field(
        sa_column=Column(
            BigInteger,
            ForeignKey("feedback_event.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    candidate_type: str = Field(max_length=64, nullable=False, index=True)
    scope: str = Field(default="workspace", max_length=32, nullable=False)
    target_user_id: Optional[int] = Field(
        default=None,
        sa_column=Column(BigInteger, nullable=True),
    )
    datasource_id: Optional[int] = Field(
        default=None,
        sa_column=Column(BigInteger, nullable=True),
    )
    proposed_content: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSONB, nullable=False, default=dict),
    )
    status: str = Field(default="candidate", max_length=32, nullable=False, index=True)
    validation_status: str = Field(default="pending", max_length=32, nullable=False)
    validation_message: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    conflict_ids: list[int] = Field(
        default_factory=list,
        sa_column=Column(JSONB, nullable=False, default=list),
    )
    activated_memory_id: Optional[int] = Field(
        default=None,
        sa_column=Column(
            BigInteger,
            ForeignKey("memory_entry.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    reviewed_by: Optional[int] = Field(
        default=None,
        sa_column=Column(BigInteger, nullable=True),
    )
    review_note: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    reviewed_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=False), nullable=True),
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        sa_column=Column(DateTime(timezone=False), nullable=False),
    )
    activated_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=False), nullable=True),
    )


class LearningJob(SQLModel, table=True):
    """Durable, idempotent processing state for each feedback event."""

    __tablename__ = "learning_job"
    __table_args__ = (UniqueConstraint("idempotency_key", name="uq_learning_job_idempotency"),)

    id: Optional[int] = Field(
        default=None,
        sa_column=Column(BigInteger, Identity(always=True), primary_key=True),
    )
    oid: int = Field(sa_column=Column(BigInteger, nullable=False, index=True))
    feedback_event_id: int = Field(
        sa_column=Column(
            BigInteger,
            ForeignKey("feedback_event.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    candidate_id: Optional[int] = Field(
        default=None,
        sa_column=Column(
            BigInteger,
            ForeignKey("learning_candidate.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    job_type: str = Field(default="extract_candidate", max_length=64, nullable=False)
    idempotency_key: str = Field(max_length=160, nullable=False)
    payload: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSONB, nullable=False, default=dict),
    )
    status: str = Field(default="pending", max_length=32, nullable=False, index=True)
    attempts: int = Field(default=0, sa_column=Column(Integer, nullable=False, default=0))
    lease_owner: Optional[str] = Field(default=None, max_length=128)
    lease_until: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=False), nullable=True),
    )
    last_error: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    created_at: datetime = Field(
        default_factory=datetime.now,
        sa_column=Column(DateTime(timezone=False), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        sa_column=Column(DateTime(timezone=False), nullable=False),
    )
