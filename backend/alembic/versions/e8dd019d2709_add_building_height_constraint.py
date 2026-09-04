"""add building height constraint

Revision ID: e8dd019d2709
Revises: 0ffecdd09558
Create Date: 2026-09-03 21:25:09.541893

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e8dd019d2709'
down_revision: Union[str, Sequence[str], None] = '0ffecdd09558'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Upgrade schema."""
    op.create_check_constraint(
        "buildings_height_non_negative",
        "buildings",
        "height >= 0"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "buildings_height_non_negative",
        "buildings",
        type_="check"
    )