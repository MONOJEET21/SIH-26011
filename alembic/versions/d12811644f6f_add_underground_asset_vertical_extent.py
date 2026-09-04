"""add underground asset vertical extent

Revision ID: d12811644f6f
Revises: 3f3527f18799
Create Date: 2026-09-03 09:44:13.817064

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd12811644f6f'
down_revision: Union[str, Sequence[str], None] = '3f3527f18799'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        'underground_assets',
        sa.Column('z_min', sa.Float(), nullable=True)
    )

    op.add_column(
        'underground_assets',
        sa.Column('z_max', sa.Float(), nullable=True)
    )

    op.add_column(
        'underground_assets',
        sa.Column('depth', sa.Float(), nullable=True)
    )

    # Give existing underground assets temporary values.
    op.execute("""
        UPDATE underground_assets
        SET z_min = 0,
            z_max = 1,
            depth = 1
        WHERE z_min IS NULL
    """)

    # Make the new columns mandatory.
    op.alter_column(
        'underground_assets',
        'z_min',
        existing_type=sa.Float(),
        nullable=False
    )

    op.alter_column(
        'underground_assets',
        'z_max',
        existing_type=sa.Float(),
        nullable=False
    )

    op.alter_column(
        'underground_assets',
        'depth',
        existing_type=sa.Float(),
        nullable=False
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column(
        'underground_assets',
        'depth'
    )

    op.drop_column(
        'underground_assets',
        'z_max'
    )

    op.drop_column(
        'underground_assets',
        'z_min'
    )