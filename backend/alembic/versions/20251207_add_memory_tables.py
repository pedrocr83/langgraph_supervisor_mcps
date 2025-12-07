"""add memory tables for semantic and procedural traces

Revision ID: 20251207_memory
Revises: 
Create Date: 2025-12-07
"""

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = "20251207_memory"
down_revision = "20251207_base"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "semantic_items",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("agent_id", sa.String(), nullable=True),
        sa.Column("conversation_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("meta", sa.JSON(), nullable=True),
        sa.Column("embedding", Vector(1024), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_semantic_items_embedding",
        "semantic_items",
        ["embedding"],
        postgresql_using="ivfflat",
        postgresql_with={"lists": 100},
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )
    op.create_index(
        "ix_semantic_items_agent_created",
        "semantic_items",
        ["agent_id", "created_at"],
    )

    op.create_table(
        "procedural_traces",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("agent_id", sa.String(), nullable=True),
        sa.Column("task_id", sa.String(), nullable=True),
        sa.Column("step", sa.Integer(), nullable=True),
        sa.Column("input", sa.Text(), nullable=True),
        sa.Column("output", sa.Text(), nullable=True),
        sa.Column("tools_used", sa.JSON(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_procedural_traces_agent_created",
        "procedural_traces",
        ["agent_id", "created_at"],
    )
    op.create_index(
        "ix_procedural_traces_task",
        "procedural_traces",
        ["task_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_procedural_traces_task", table_name="procedural_traces")
    op.drop_index("ix_procedural_traces_agent_created", table_name="procedural_traces")
    op.drop_table("procedural_traces")

    op.drop_index("ix_semantic_items_agent_created", table_name="semantic_items")
    op.drop_index("ix_semantic_items_embedding", table_name="semantic_items")
    op.drop_table("semantic_items")

