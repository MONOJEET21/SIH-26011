"""add property unit area constraint

Revision ID: 2c5afe2627c6
Revises: 7bdbfcbefafd
Create Date: 2026-09-03 21:23:14.926052

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2c5afe2627c6'
down_revision: Union[str, Sequence[str], None] = '7bdbfcbefafd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_check_constraint(
        "property_units_area_non_negative",
        "property_units",
        "area >= 0"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "property_units_area_non_negative",
        "property_units",
        type_="check"
    )