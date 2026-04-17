"""Merge multiple heads

Revision ID: 7694897178ec
Revises: 002_bank_budget, 8b08314e19ad
Create Date: 2026-04-17 22:47:32.801887

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7694897178ec'
down_revision: Union[str, Sequence[str], None] = ('002_bank_budget', '8b08314e19ad')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
