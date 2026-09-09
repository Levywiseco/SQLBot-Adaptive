from datetime import datetime
from typing import Any, Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
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


class MemoryEntry(SQLModel, table=True):
    """A governed memory that can participate in future prompts."""

    __tablename__ = "memory_entry"

    id: Optional[int] = Field(
        default=None,
        sa_column=Column(BigInteger, Identity(always=True), primary_key=True),
    )
    oid: int = Field(sa_column=Column(BigInteger, nullable=False, index=True))
    owner_user_id: Optional[int] = Field(
        default=None,
        sa_column=Column(BigInteger, nullable=True, index=True),
    )
    created_by: int = Field(sa_column=Column(BigInteger, nullable=False))
    datasource_id: Optional[int] = Field(
        default=None,
        sa_column=Column(
            BigInteger,
            ForeignKey("core_datasource.id", ondelete="RESTRICT"),
            nullable=True,
            index=True,
        ),
    )
    scope: str = Field(default="personal", max_length=32, nullable=False)
    memory_type: str = Field(default="preference", max_length=64, nullable=False)
    title: str = Field(max_length=255, nullable=False)
    content: str = Field(sa_column=Column(Text, nullable=False))
    keywords: list[str] = Field(
        default_factory=list,
        sa_column=Column(JSONB, nullable=False, default=list),
    )
    dependencies: list[str] = Field(
        default_factory=list,
        sa_column=Column(JSONB, nullable=False, default=list),
    )
    status: str = Field(default="active", max_length=32, nullable=False, index=True)
    source_type: str = Field(default="manual", max_length=64, nullable=False)
    source_reference_id: Optional[str] = Field(default=None, max_length=128)
    fingerprint: str = Field(max_length=64, nullable=False, index=True)
    version: int = Field(default=1, sa_column=Column(Integer, nullable=False, default=1))
    priority: int = Field(default=0, sa_column=Column(Integer, nullable=False, default=0))
    usage_count: int = Field(default=0, sa_column=Column(Integer, nullable=False, default=0))
    last_used_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=False), nullable=True),
    )
    expires_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=False), nullable=True),
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        sa_column=Column(DateTime(timezone=False), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        sa_column=Column(DateTime(timezone=False), nullable=False),
    )


class ChatContextState(SQLModel, table=True):
    """Structured state retained inside one chat for short follow-up questions."""

    __tablename__ = "chat_context_state"

    chat_id: int = Field(
        sa_column=Column(
            BigInteger,
            ForeignKey("chat.id", ondelete="CASCADE"),
            primary_key=True,
        )
    )
    oid: int = Field(sa_column=Column(BigInteger, nullable=False, index=True))
    user_id: int = Field(sa_column=Column(BigInteger, nullable=False, index=True))
    datasource_id: Optional[int] = Field(
        default=None,
        sa_column=Column(BigInteger, nullable=True),
    )
    metric_refs: list[dict[str, Any]] = Field(
        default_factory=list,
        sa_column=Column(JSONB, nullable=False, default=list),
    )
    filters: list[dict[str, Any]] = Field(
        default_factory=list,
        sa_column=Column(JSONB, nullable=False, default=list),
    )
    time_range: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSONB, nullable=False, default=dict),
    )
    last_record_id: Optional[int] = Field(
        default=None,
        sa_column=Column(BigInteger, nullable=True),
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        sa_column=Column(DateTime(timezone=False), nullable=False),
    )


class RetrievalTrace(SQLModel, table=True):
    """Knowledge provenance used for a concrete chat answer."""

    __tablename__ = "retrieval_trace"
    __table_args__ = (UniqueConstraint("chat_record_id", name="uq_retrieval_trace_record"),)

    id: Optional[int] = Field(
        default=None,
        sa_column=Column(BigInteger, Identity(always=True), primary_key=True),
    )
    chat_record_id: int = Field(
        sa_column=Column(
            BigInteger,
            ForeignKey("chat_record.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    oid: int = Field(sa_column=Column(BigInteger, nullable=False, index=True))
    user_id: int = Field(sa_column=Column(BigInteger, nullable=False))
    datasource_id: Optional[int] = Field(
        default=None,
        sa_column=Column(BigInteger, nullable=True),
    )
    question: str = Field(sa_column=Column(Text, nullable=False))
    metric_refs: list[dict[str, Any]] = Field(
        default_factory=list,
        sa_column=Column(JSONB, nullable=False, default=list),
    )
    memory_refs: list[dict[str, Any]] = Field(
        default_factory=list,
        sa_column=Column(JSONB, nullable=False, default=list),
    )
    inherited_metric: bool = Field(
        default=False,
        sa_column=Column(Boolean, nullable=False, default=False),
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        sa_column=Column(DateTime(timezone=False), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        sa_column=Column(DateTime(timezone=False), nullable=False),
    )
