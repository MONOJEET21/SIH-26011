"""add study area timestamps

Revision ID: c00d189bb8fd
Revises: 283e367fd086
Create Date: 2026-09-03 15:41:42.186877

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c00d189bb8fd"
down_revision: Union[str, Sequence[str], None] = "283e367fd086"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "study_areas",
        sa.Column("created_at", sa.DateTime(), nullable=True)
    )

    op.add_column(
        "study_areas",
        sa.Column("updated_at", sa.DateTime(), nullable=True)
    )

    # Give existing study areas timestamps.
    op.execute("""
        UPDATE study_areas
        SET created_at = CURRENT_TIMESTAMP,
            updated_at = CURRENT_TIMESTAMP
        WHERE created_at IS NULL
           OR updated_at IS NULL
    """)

    # Make timestamps mandatory.
    op.alter_column(
        "study_areas",
        "created_at",
        existing_type=sa.DateTime(),
        nullable=False
    )

    op.alter_column(
        "study_areas",
        "updated_at",
        existing_type=sa.DateTime(),
        nullable=False
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column("study_areas", "updated_at")
    op.drop_column("study_areas", "created_at")