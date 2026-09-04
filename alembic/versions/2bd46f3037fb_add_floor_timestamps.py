"""add floor timestamps

Revision ID: 2bd46f3037fb
Revises: b015159b0f72
Create Date: 2026-09-03 11:03:17.533667

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2bd46f3037fb"
down_revision: Union[str, Sequence[str], None] = "b015159b0f72"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "floors",
        sa.Column("created_at", sa.DateTime(), nullable=True)
    )

    op.add_column(
        "floors",
        sa.Column("updated_at", sa.DateTime(), nullable=True)
    )

    # Give existing floors timestamps.
    op.execute("""
        UPDATE floors
        SET created_at = CURRENT_TIMESTAMP,
            updated_at = CURRENT_TIMESTAMP
        WHERE created_at IS NULL
           OR updated_at IS NULL
    """)

    # Make the columns mandatory.
    op.alter_column(
        "floors",
        "created_at",
        existing_type=sa.DateTime(),
        nullable=False
    )

    op.alter_column(
        "floors",
        "updated_at",
        existing_type=sa.DateTime(),
        nullable=False
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column("floors", "updated_at")
    op.drop_column("floors", "created_at")