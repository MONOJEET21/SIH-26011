"""add building timestamps

Revision ID: b015159b0f72
Revises: c17b5ded45fb
Create Date: 2026-09-03 10:59:50.322967

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b015159b0f72"
down_revision: Union[str, Sequence[str], None] = "c17b5ded45fb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "buildings",
        sa.Column("created_at", sa.DateTime(), nullable=True)
    )

    op.add_column(
        "buildings",
        sa.Column("updated_at", sa.DateTime(), nullable=True)
    )

    # Give existing buildings timestamps.
    op.execute("""
        UPDATE buildings
        SET created_at = CURRENT_TIMESTAMP,
            updated_at = CURRENT_TIMESTAMP
        WHERE created_at IS NULL
           OR updated_at IS NULL
    """)

    # Make the columns mandatory.
    op.alter_column(
        "buildings",
        "created_at",
        existing_type=sa.DateTime(),
        nullable=False
    )

    op.alter_column(
        "buildings",
        "updated_at",
        existing_type=sa.DateTime(),
        nullable=False
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column("buildings", "updated_at")
    op.drop_column("buildings", "created_at")