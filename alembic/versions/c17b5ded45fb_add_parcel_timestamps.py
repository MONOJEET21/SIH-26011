"""add parcel timestamps

Revision ID: c17b5ded45fb
Revises: f15d8e40fa0d
Create Date: 2026-09-03 10:56:28.978292

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c17b5ded45fb"
down_revision: Union[str, Sequence[str], None] = "f15d8e40fa0d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "parcels",
        sa.Column("created_at", sa.DateTime(), nullable=True)
    )

    op.add_column(
        "parcels",
        sa.Column("updated_at", sa.DateTime(), nullable=True)
    )

    # Give existing parcels timestamps.
    op.execute("""
        UPDATE parcels
        SET created_at = CURRENT_TIMESTAMP,
            updated_at = CURRENT_TIMESTAMP
        WHERE created_at IS NULL
           OR updated_at IS NULL
    """)

    # Make the columns mandatory.
    op.alter_column(
        "parcels",
        "created_at",
        existing_type=sa.DateTime(),
        nullable=False
    )

    op.alter_column(
        "parcels",
        "updated_at",
        existing_type=sa.DateTime(),
        nullable=False
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column("parcels", "updated_at")
    op.drop_column("parcels", "created_at")