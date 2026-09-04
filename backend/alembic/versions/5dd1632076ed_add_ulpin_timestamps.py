"""add ulpin timestamps

Revision ID: 5dd1632076ed
Revises: 44160adefacf
Create Date: 2026-09-03 11:45:08.315006

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "5dd1632076ed"
down_revision: Union[str, Sequence[str], None] = "44160adefacf"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "ulpins",
        sa.Column("created_at", sa.DateTime(), nullable=True)
    )

    op.add_column(
        "ulpins",
        sa.Column("updated_at", sa.DateTime(), nullable=True)
    )

    # Give existing ULPIN records timestamps.
    op.execute("""
        UPDATE ulpins
        SET created_at = CURRENT_TIMESTAMP,
            updated_at = CURRENT_TIMESTAMP
        WHERE created_at IS NULL
           OR updated_at IS NULL
    """)

    # Make the columns mandatory.
    op.alter_column(
        "ulpins",
        "created_at",
        existing_type=sa.DateTime(),
        nullable=False
    )

    op.alter_column(
        "ulpins",
        "updated_at",
        existing_type=sa.DateTime(),
        nullable=False
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column("ulpins", "updated_at")
    op.drop_column("ulpins", "created_at")