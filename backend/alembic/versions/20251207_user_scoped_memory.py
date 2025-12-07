"""add user_id scope to memory tables

Revision ID: 20251207_user_scope
Revises: 20251207_memory
Create Date: 2025-12-07
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20251207_user_scope"
down_revision = "20251207_memory"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "semantic_items",
        sa.Column("user_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "semantic_items_user_id_fkey",
        "semantic_items",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(
        "ix_semantic_items_user_created",
        "semantic_items",
        ["user_id", "created_at"],
    )

    op.add_column(
        "procedural_traces",
        sa.Column("user_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "procedural_traces_user_id_fkey",
        "procedural_traces",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(
        "ix_procedural_traces_user_created",
        "procedural_traces",
        ["user_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_procedural_traces_user_created", table_name="procedural_traces")
    op.drop_constraint("procedural_traces_user_id_fkey", "procedural_traces", type_="foreignkey")
    op.drop_column("procedural_traces", "user_id")

    op.drop_index("ix_semantic_items_user_created", table_name="semantic_items")
    op.drop_constraint("semantic_items_user_id_fkey", "semantic_items", type_="foreignkey")
    op.drop_column("semantic_items", "user_id")

