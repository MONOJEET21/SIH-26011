"""add underground asset timestamps

Revision ID: 44160adefacf
Revises: 62a5709785b3
Create Date: 2026-09-03 11:41:31.278135

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "44160adefacf"
down_revision: Union[str, Sequence[str], None] = "62a5709785b3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "underground_assets",
        sa.Column("created_at", sa.DateTime(), nullable=True)
    )

    op.add_column(
        "underground_assets",
        sa.Column("updated_at", sa.DateTime(), nullable=True)
    )

    # Give existing underground assets timestamps.
    op.execute("""
        UPDATE underground_assets
        SET created_at = CURRENT_TIMESTAMP,
            updated_at = CURRENT_TIMESTAMP
        WHERE created_at IS NULL
           OR updated_at IS NULL
    """)

    # Make the columns mandatory.
    op.alter_column(
        "underground_assets",
        "created_at",
        existing_type=sa.DateTime(),
        nullable=False
    )

    op.alter_column(
        "underground_assets",
        "updated_at",
        existing_type=sa.DateTime(),
        nullable=False
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column("underground_assets", "updated_at")
    op.drop_column("underground_assets", "created_at")