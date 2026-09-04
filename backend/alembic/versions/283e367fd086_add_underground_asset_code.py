"""add underground asset code

Revision ID: 283e367fd086
Revises: 0f7eaf7c0900
Create Date: 2026-09-03 15:30:55.392809

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "283e367fd086"
down_revision: Union[str, Sequence[str], None] = "0f7eaf7c0900"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "underground_assets",
        sa.Column(
            "asset_code",
            sa.String(length=100),
            nullable=True
        )
    )

    # Give existing underground assets a temporary code.
    op.execute("""
        UPDATE underground_assets
        SET asset_code = 'ASSET-' || id
        WHERE asset_code IS NULL
    """)

    # Make asset_code mandatory.
    op.alter_column(
        "underground_assets",
        "asset_code",
        existing_type=sa.String(length=100),
        nullable=False
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column(
        "underground_assets",
        "asset_code"
    )