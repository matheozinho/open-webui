"""Add user_learning_progress table for Learning Orchestrator

Revision ID: learning_progress_001
Revises: add_user_profiles_001
Create Date: 2026-04-19

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "learning_progress_001"
down_revision: Union[str, None] = "add_user_profiles_001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create user_learning_progress table
    op.create_table(
        "user_learning_progress",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("current_step", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("step_data", postgresql.JSONB(), nullable=True),
        sa.Column("last_step_at", sa.BigInteger(), nullable=True),
        sa.Column("completed_at", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.BigInteger(), nullable=False),
        sa.Column("updated_at", sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_user_learning_progress"),
        sa.UniqueConstraint("user_id", name="uq_user_learning_progress_user_id"),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], name="fk_user_learning_progress_user_id"),
    )

    # Create index for fast user lookups
    op.create_index(
        "ix_user_learning_progress_user_id",
        "user_learning_progress",
        ["user_id"],
        unique=False,
    )
    
    # Add check constraint for step values (1-6)
    op.create_check_constraint(
        "ck_user_learning_progress_step_range",
        "user_learning_progress",
        "current_step >= 1 AND current_step <= 6",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_user_learning_progress_step_range",
        "user_learning_progress",
        type_="check",
    )
    op.drop_index("ix_user_learning_progress_user_id", table_name="user_learning_progress")
    op.drop_table("user_learning_progress")
