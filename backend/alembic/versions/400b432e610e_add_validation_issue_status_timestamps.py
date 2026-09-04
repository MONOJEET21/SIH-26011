"""add validation issue status timestamps

Revision ID: 400b432e610e
Revises: 80144c92c53f
Create Date: 2026-09-03 14:53:36.374688

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "400b432e610e"
down_revision: Union[str, Sequence[str], None] = "80144c92c53f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "validation_issues",
        sa.Column("status", sa.String(length=50), nullable=True)
    )

    op.add_column(
        "validation_issues",
        sa.Column("created_at", sa.DateTime(), nullable=True)
    )

    op.add_column(
        "validation_issues",
        sa.Column("updated_at", sa.DateTime(), nullable=True)
    )

    # Give existing validation issues safe initial values.
    op.execute("""
        UPDATE validation_issues
        SET status = 'OPEN',
            created_at = CURRENT_TIMESTAMP,
            updated_at = CURRENT_TIMESTAMP
        WHERE status IS NULL
           OR created_at IS NULL
           OR updated_at IS NULL
    """)

    # Make the new fields mandatory.
    op.alter_column(
        "validation_issues",
        "status",
        existing_type=sa.String(length=50),
        nullable=False
    )

    op.alter_column(
        "validation_issues",
        "created_at",
        existing_type=sa.DateTime(),
        nullable=False
    )

    op.alter_column(
        "validation_issues",
        "updated_at",
        existing_type=sa.DateTime(),
        nullable=False
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column("validation_issues", "updated_at")
    op.drop_column("validation_issues", "created_at")
    op.drop_column("validation_issues", "status")