"""Add user_profiles table for UIMA (User Identity & Memory Architecture)

Revision ID: add_user_profiles_001
Revises: d31026856c01
Create Date: 2025-01-25

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'add_user_profiles_001'
down_revision = 'd31026856c01'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create the user_profiles table
    op.create_table(
        'user_profiles',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('job', sa.String(255), nullable=True, comment='Job title or profession'),
        sa.Column('tone_preference', sa.String(100), nullable=True, comment='Preferred communication tone (e.g., formal, casual, technical)'),
        sa.Column('project_context', sa.Text(), nullable=True, comment='Current project context or domain knowledge'),
        sa.Column('preferences', sa.JSON(), nullable=True, comment='Additional preferences stored as JSON'),
        sa.Column('created_at', sa.BigInteger(), nullable=False),
        sa.Column('updated_at', sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE')
    )
    
    # Create index on user_id for efficient lookups
    op.create_index(
        'ix_user_profiles_user_id',
        'user_profiles',
        ['user_id']
    )


def downgrade() -> None:
    # Drop the index
    op.drop_index('ix_user_profiles_user_id', table_name='user_profiles')
    
    # Drop the table
    op.drop_table('user_profiles')
