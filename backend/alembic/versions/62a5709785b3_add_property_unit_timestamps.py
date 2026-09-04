"""add property unit timestamps

Revision ID: 62a5709785b3
Revises: 2bd46f3037fb
Create Date: 2026-09-03 11:33:01.511642

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "62a5709785b3"
down_revision: Union[str, Sequence[str], None] = "2bd46f3037fb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "property_units",
        sa.Column("created_at", sa.DateTime(), nullable=True)
    )

    op.add_column(
        "property_units",
        sa.Column("updated_at", sa.DateTime(), nullable=True)
    )

    # Give existing property units timestamps.
    op.execute("""
        UPDATE property_units
        SET created_at = CURRENT_TIMESTAMP,
            updated_at = CURRENT_TIMESTAMP
        WHERE created_at IS NULL
           OR updated_at IS NULL
    """)

    # Make the columns mandatory.
    op.alter_column(
        "property_units",
        "created_at",
        existing_type=sa.DateTime(),
        nullable=False
    )

    op.alter_column(
        "property_units",
        "updated_at",
        existing_type=sa.DateTime(),
        nullable=False
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column("property_units", "updated_at")
    op.drop_column("property_units", "created_at")