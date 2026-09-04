"""add property unit code

Revision ID: 7a024e5b1d87
Revises: 2cdd71a5515a
Create Date: 2026-09-03 10:26:20.469069

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7a024e5b1d87'
down_revision: Union[str, Sequence[str], None] = '2cdd71a5515a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        'property_units',
        sa.Column('unit_code', sa.String(length=100), nullable=True)
    )

    # Give existing property units a temporary unit code.
    op.execute("""
        UPDATE property_units
        SET unit_code = 'UNIT-' || id::text
        WHERE unit_code IS NULL
    """)

    # Make unit_code mandatory.
    op.alter_column(
        'property_units',
        'unit_code',
        existing_type=sa.String(length=100),
        nullable=False
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column(
        'property_units',
        'unit_code'
    )