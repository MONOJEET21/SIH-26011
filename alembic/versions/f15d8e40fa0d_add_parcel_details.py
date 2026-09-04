"""add parcel details

Revision ID: f15d8e40fa0d
Revises: 50edd3d51079
Create Date: 2026-09-03 10:45:42.426032

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f15d8e40fa0d'
down_revision: Union[str, Sequence[str], None] = '50edd3d51079'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        'parcels',
        sa.Column('parcel_code', sa.String(length=100), nullable=True)
    )

    op.add_column(
        'parcels',
        sa.Column('area', sa.Float(), nullable=True)
    )

    op.add_column(
        'parcels',
        sa.Column('land_use', sa.String(length=100), nullable=True)
    )

    op.add_column(
        'parcels',
        sa.Column('status', sa.String(length=50), nullable=True)
    )

    # Give existing parcels temporary values.
    op.execute("""
        UPDATE parcels
        SET parcel_code = 'PARCEL-' || id::text,
            area = 0,
            land_use = 'UNKNOWN',
            status = 'ACTIVE'
        WHERE parcel_code IS NULL
    """)

    # Make the new columns mandatory.
    op.alter_column(
        'parcels',
        'parcel_code',
        existing_type=sa.String(length=100),
        nullable=False
    )

    op.alter_column(
        'parcels',
        'area',
        existing_type=sa.Float(),
        nullable=False
    )

    op.alter_column(
        'parcels',
        'land_use',
        existing_type=sa.String(length=100),
        nullable=False
    )

    op.alter_column(
        'parcels',
        'status',
        existing_type=sa.String(length=50),
        nullable=False
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column(
        'parcels',
        'status'
    )

    op.drop_column(
        'parcels',
        'land_use'
    )

    op.drop_column(
        'parcels',
        'area'
    )

    op.drop_column(
        'parcels',
        'parcel_code'
    )