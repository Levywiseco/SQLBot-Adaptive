"""Add versioned metric catalog.

Revision ID: 72a1d9c4f001
Revises: a2e2ecfa5a9c
Create Date: 2026-09-09
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "72a1d9c4f001"
down_revision = "a2e2ecfa5a9c"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "metric_definition",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("oid", sa.BigInteger(), nullable=False),
        sa.Column("code", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("aliases", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("datasource_id", sa.BigInteger(), nullable=False),
        sa.Column("owner_user_id", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="draft", nullable=False),
        sa.Column("current_version_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["datasource_id"], ["core_datasource.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("oid", "code", name="uq_metric_definition_oid_code"),
    )
    op.create_index("ix_metric_definition_oid", "metric_definition", ["oid"])
    op.create_index("ix_metric_definition_datasource_id", "metric_definition", ["datasource_id"])

    op.create_table(
        "metric_version",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("metric_id", sa.BigInteger(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("expression", sa.Text(), nullable=False),
        sa.Column("aggregation", sa.String(length=32), server_default="SUM", nullable=False),
        sa.Column("time_field", sa.String(length=255), nullable=True),
        sa.Column("grain", sa.String(length=128), nullable=True),
        sa.Column("required_tables", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("dimensions", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("filters", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("join_rules", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("unit", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=32), server_default="draft", nullable=False),
        sa.Column("validation_status", sa.String(length=32), server_default="pending", nullable=False),
        sa.Column("validation_message", sa.Text(), nullable=True),
        sa.Column("effective_from", sa.DateTime(), nullable=True),
        sa.Column("effective_to", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("reviewed_by", sa.BigInteger(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("review_note", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["metric_id"], ["metric_definition.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("metric_id", "version", name="uq_metric_version_number"),
    )
    op.create_index("ix_metric_version_metric_id", "metric_version", ["metric_id"])
    op.create_index("ix_metric_version_status", "metric_version", ["status"])
    op.create_foreign_key(
        "fk_metric_definition_current_version",
        "metric_definition",
        "metric_version",
        ["current_version_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade():
    op.drop_constraint(
        "fk_metric_definition_current_version",
        "metric_definition",
        type_="foreignkey",
    )
    op.drop_index("ix_metric_version_status", table_name="metric_version")
    op.drop_index("ix_metric_version_metric_id", table_name="metric_version")
    op.drop_table("metric_version")
    op.drop_index("ix_metric_definition_datasource_id", table_name="metric_definition")
    op.drop_index("ix_metric_definition_oid", table_name="metric_definition")
    op.drop_table("metric_definition")
