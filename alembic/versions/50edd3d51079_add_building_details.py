"""add building details

Revision ID: 50edd3d51079
Revises: 7a024e5b1d87
Create Date: 2026-09-03 10:32:54.588380

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '50edd3d51079'
down_revision: Union[str, Sequence[str], None] = '7a024e5b1d87'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        'buildings',
        sa.Column('building_code', sa.String(length=100), nullable=True)
    )

    op.add_column(
        'buildings',
        sa.Column('ground_elevation', sa.Float(), nullable=True)
    )

    op.add_column(
        'buildings',
        sa.Column('height', sa.Float(), nullable=True)
    )

    op.add_column(
        'buildings',
        sa.Column('floor_count', sa.Integer(), nullable=True)
    )

    op.add_column(
        'buildings',
        sa.Column('building_type', sa.String(length=100), nullable=True)
    )

    op.add_column(
        'buildings',
        sa.Column('status', sa.String(length=50), nullable=True)
    )

    # Give existing buildings temporary values.
    op.execute("""
        UPDATE buildings
        SET building_code = 'BUILDING-' || id::text,
            ground_elevation = 0,
            height = 3,
            floor_count = 1,
            building_type = 'UNKNOWN',
            status = 'ACTIVE'
        WHERE building_code IS NULL
    """)

    # Make the new columns mandatory.
    op.alter_column(
        'buildings',
        'building_code',
        existing_type=sa.String(length=100),
        nullable=False
    )

    op.alter_column(
        'buildings',
        'ground_elevation',
        existing_type=sa.Float(),
        nullable=False
    )

    op.alter_column(
        'buildings',
        'height',
        existing_type=sa.Float(),
        nullable=False
    )

    op.alter_column(
        'buildings',
        'floor_count',
        existing_type=sa.Integer(),
        nullable=False
    )

    op.alter_column(
        'buildings',
        'building_type',
        existing_type=sa.String(length=100),
        nullable=False
    )

    op.alter_column(
        'buildings',
        'status',
        existing_type=sa.String(length=50),
        nullable=False
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column(
        'buildings',
        'status'
    )

    op.drop_column(
        'buildings',
        'building_type'
    )

    op.drop_column(
        'buildings',
        'floor_count'
    )

    op.drop_column(
        'buildings',
        'height'
    )

    op.drop_column(
        'buildings',
        'ground_elevation'
    )

    op.drop_column(
        'buildings',
        'building_code'
    )