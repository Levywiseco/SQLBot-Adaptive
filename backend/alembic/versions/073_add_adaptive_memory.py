"""Add governed memory, feedback and learning tables.

Revision ID: b82d1e7a3001
Revises: 72a1d9c4f001
Create Date: 2026-09-09
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "b82d1e7a3001"
down_revision = "72a1d9c4f001"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "memory_entry",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("oid", sa.BigInteger(), nullable=False),
        sa.Column("owner_user_id", sa.BigInteger(), nullable=True),
        sa.Column("created_by", sa.BigInteger(), nullable=False),
        sa.Column("datasource_id", sa.BigInteger(), nullable=True),
        sa.Column("scope", sa.String(length=32), server_default="personal", nullable=False),
        sa.Column("memory_type", sa.String(length=64), server_default="preference", nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("keywords", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("dependencies", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="active", nullable=False),
        sa.Column("source_type", sa.String(length=64), server_default="manual", nullable=False),
        sa.Column("source_reference_id", sa.String(length=128), nullable=True),
        sa.Column("fingerprint", sa.String(length=64), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("priority", sa.Integer(), server_default="0", nullable=False),
        sa.Column("usage_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["datasource_id"], ["core_datasource.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_memory_entry_oid", "memory_entry", ["oid"])
    op.create_index("ix_memory_entry_owner_user_id", "memory_entry", ["owner_user_id"])
    op.create_index("ix_memory_entry_datasource_id", "memory_entry", ["datasource_id"])
    op.create_index("ix_memory_entry_status", "memory_entry", ["status"])
    op.create_index("ix_memory_entry_fingerprint", "memory_entry", ["fingerprint"])

    op.create_table(
        "chat_context_state",
        sa.Column("chat_id", sa.BigInteger(), nullable=False),
        sa.Column("oid", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("datasource_id", sa.BigInteger(), nullable=True),
        sa.Column("metric_refs", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("filters", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("time_range", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("last_record_id", sa.BigInteger(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["chat_id"], ["chat.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("chat_id"),
    )
    op.create_index("ix_chat_context_state_oid", "chat_context_state", ["oid"])
    op.create_index("ix_chat_context_state_user_id", "chat_context_state", ["user_id"])

    op.create_table(
        "retrieval_trace",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("chat_record_id", sa.BigInteger(), nullable=False),
        sa.Column("oid", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("datasource_id", sa.BigInteger(), nullable=True),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("metric_refs", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("memory_refs", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("inherited_metric", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["chat_record_id"], ["chat_record.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("chat_record_id", name="uq_retrieval_trace_record"),
    )
    op.create_index("ix_retrieval_trace_chat_record_id", "retrieval_trace", ["chat_record_id"])
    op.create_index("ix_retrieval_trace_oid", "retrieval_trace", ["oid"])

    op.create_table(
        "feedback_event",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("oid", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("chat_record_id", sa.BigInteger(), nullable=False),
        sa.Column("feedback_type", sa.String(length=64), nullable=False),
        sa.Column("correction_text", sa.Text(), nullable=True),
        sa.Column("memory_title", sa.String(length=255), nullable=True),
        sa.Column("memory_content", sa.Text(), nullable=True),
        sa.Column("memory_keywords", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("answer_snapshot", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="recorded", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("processed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["chat_record_id"], ["chat_record.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("oid", "user_id", "idempotency_key", name="uq_feedback_idempotency"),
    )
    op.create_index("ix_feedback_event_oid", "feedback_event", ["oid"])
    op.create_index("ix_feedback_event_user_id", "feedback_event", ["user_id"])
    op.create_index("ix_feedback_event_chat_record_id", "feedback_event", ["chat_record_id"])
    op.create_index("ix_feedback_event_feedback_type", "feedback_event", ["feedback_type"])

    op.create_table(
        "learning_candidate",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("oid", sa.BigInteger(), nullable=False),
        sa.Column("feedback_event_id", sa.BigInteger(), nullable=False),
        sa.Column("candidate_type", sa.String(length=64), nullable=False),
        sa.Column("scope", sa.String(length=32), server_default="workspace", nullable=False),
        sa.Column("target_user_id", sa.BigInteger(), nullable=True),
        sa.Column("datasource_id", sa.BigInteger(), nullable=True),
        sa.Column("proposed_content", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="candidate", nullable=False),
        sa.Column("validation_status", sa.String(length=32), server_default="pending", nullable=False),
        sa.Column("validation_message", sa.Text(), nullable=True),
        sa.Column("conflict_ids", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("activated_memory_id", sa.BigInteger(), nullable=True),
        sa.Column("reviewed_by", sa.BigInteger(), nullable=True),
        sa.Column("review_note", sa.Text(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("activated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["feedback_event_id"], ["feedback_event.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["activated_memory_id"], ["memory_entry.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("feedback_event_id", name="uq_learning_candidate_feedback"),
    )
    op.create_index("ix_learning_candidate_oid", "learning_candidate", ["oid"])
    op.create_index("ix_learning_candidate_feedback_event_id", "learning_candidate", ["feedback_event_id"])
    op.create_index("ix_learning_candidate_candidate_type", "learning_candidate", ["candidate_type"])
    op.create_index("ix_learning_candidate_status", "learning_candidate", ["status"])

    op.create_table(
        "learning_job",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("oid", sa.BigInteger(), nullable=False),
        sa.Column("feedback_event_id", sa.BigInteger(), nullable=False),
        sa.Column("candidate_id", sa.BigInteger(), nullable=True),
        sa.Column("job_type", sa.String(length=64), server_default="extract_candidate", nullable=False),
        sa.Column("idempotency_key", sa.String(length=160), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="pending", nullable=False),
        sa.Column("attempts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("lease_owner", sa.String(length=128), nullable=True),
        sa.Column("lease_until", sa.DateTime(), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["feedback_event_id"], ["feedback_event.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["candidate_id"], ["learning_candidate.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key", name="uq_learning_job_idempotency"),
    )
    op.create_index("ix_learning_job_oid", "learning_job", ["oid"])
    op.create_index("ix_learning_job_feedback_event_id", "learning_job", ["feedback_event_id"])
    op.create_index("ix_learning_job_status", "learning_job", ["status"])


def downgrade():
    op.drop_index("ix_learning_job_status", table_name="learning_job")
    op.drop_index("ix_learning_job_feedback_event_id", table_name="learning_job")
    op.drop_index("ix_learning_job_oid", table_name="learning_job")
    op.drop_table("learning_job")
    op.drop_index("ix_learning_candidate_status", table_name="learning_candidate")
    op.drop_index("ix_learning_candidate_candidate_type", table_name="learning_candidate")
    op.drop_index("ix_learning_candidate_feedback_event_id", table_name="learning_candidate")
    op.drop_index("ix_learning_candidate_oid", table_name="learning_candidate")
    op.drop_table("learning_candidate")
    op.drop_index("ix_feedback_event_feedback_type", table_name="feedback_event")
    op.drop_index("ix_feedback_event_chat_record_id", table_name="feedback_event")
    op.drop_index("ix_feedback_event_user_id", table_name="feedback_event")
    op.drop_index("ix_feedback_event_oid", table_name="feedback_event")
    op.drop_table("feedback_event")
    op.drop_index("ix_retrieval_trace_oid", table_name="retrieval_trace")
    op.drop_index("ix_retrieval_trace_chat_record_id", table_name="retrieval_trace")
    op.drop_table("retrieval_trace")
    op.drop_index("ix_chat_context_state_user_id", table_name="chat_context_state")
    op.drop_index("ix_chat_context_state_oid", table_name="chat_context_state")
    op.drop_table("chat_context_state")
    op.drop_index("ix_memory_entry_fingerprint", table_name="memory_entry")
    op.drop_index("ix_memory_entry_status", table_name="memory_entry")
    op.drop_index("ix_memory_entry_datasource_id", table_name="memory_entry")
    op.drop_index("ix_memory_entry_owner_user_id", table_name="memory_entry")
    op.drop_index("ix_memory_entry_oid", table_name="memory_entry")
    op.drop_table("memory_entry")
