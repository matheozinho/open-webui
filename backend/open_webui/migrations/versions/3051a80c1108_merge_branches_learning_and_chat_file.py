"""Merge branches learning and chat_file

Revision ID: 3051a80c1108
Revises: learning_progress_001, c440947495f3
Create Date: 2026-04-19 12:29:22.275949

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import open_webui.internal.db


# revision identifiers, used by Alembic.
revision: str = '3051a80c1108'
down_revision: Union[str, None] = ('learning_progress_001', 'c440947495f3')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
