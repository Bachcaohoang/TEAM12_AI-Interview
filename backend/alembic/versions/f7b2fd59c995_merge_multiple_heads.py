"""merge_multiple_heads

Revision ID: f7b2fd59c995
Revises: 87b27869ab7d, c8a5fbd42804
Create Date: 2026-11-23 09:07:21.737815

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f7b2fd59c995'
down_revision: Union[str, Sequence[str], None] = ('87b27869ab7d', 'c8a5fbd42804')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
