"""add property unit volume constraint

Revision ID: 0ffecdd09558
Revises: 2c5afe2627c6
Create Date: 2026-09-03 21:24:09.451310

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0ffecdd09558'
down_revision: Union[str, Sequence[str], None] = '2c5afe2627c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_check_constraint(
        "property_units_volume_non_negative",
        "property_units",
        "volume >= 0"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "property_units_volume_non_negative",
        "property_units",
        type_="check"
    )