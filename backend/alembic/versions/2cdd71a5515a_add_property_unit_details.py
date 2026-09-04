"""add property unit details

Revision ID: 2cdd71a5515a
Revises: bfcc14ca620e
Create Date: 2026-09-03 10:10:52.012878

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2cdd71a5515a'
down_revision: Union[str, Sequence[str], None] = 'bfcc14ca620e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        'property_units',
        sa.Column('area', sa.Float(), nullable=True)
    )

    op.add_column(
        'property_units',
        sa.Column('volume', sa.Float(), nullable=True)
    )

    op.add_column(
        'property_units',
        sa.Column('ownership_status', sa.String(length=100), nullable=True)
    )

    op.add_column(
        'property_units',
        sa.Column('status', sa.String(length=50), nullable=True)
    )

    # Give existing property units temporary values.
    op.execute("""
        UPDATE property_units
        SET area = 0,
            volume = 0,
            ownership_status = 'UNKNOWN',
            status = 'ACTIVE'
        WHERE area IS NULL
    """)

    # Make the new columns mandatory.
    op.alter_column(
        'property_units',
        'area',
        existing_type=sa.Float(),
        nullable=False
    )

    op.alter_column(
        'property_units',
        'volume',
        existing_type=sa.Float(),
        nullable=False
    )

    op.alter_column(
        'property_units',
        'ownership_status',
        existing_type=sa.String(length=100),
        nullable=False
    )

    op.alter_column(
        'property_units',
        'status',
        existing_type=sa.String(length=50),
        nullable=False
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column(
        'property_units',
        'status'
    )

    op.drop_column(
        'property_units',
        'ownership_status'
    )

    op.drop_column(
        'property_units',
        'volume'
    )

    op.drop_column(
        'property_units',
        'area'
    )