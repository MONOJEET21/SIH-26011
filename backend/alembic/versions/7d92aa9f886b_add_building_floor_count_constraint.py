"""add building floor count constraint

Revision ID: 7d92aa9f886b
Revises: e8dd019d2709
Create Date: 2026-09-03 21:26:52.975268

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7d92aa9f886b'
down_revision: Union[str, Sequence[str], None] = 'e8dd019d2709'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_check_constraint(
        "buildings_floor_count_non_negative",
        "buildings",
        "floor_count >= 0"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "buildings_floor_count_non_negative",
        "buildings",
        type_="check"
    )