"""add validation issue entity fields

Revision ID: 80144c92c53f
Revises: 5dd1632076ed
Create Date: 2026-09-03 14:39:39.097172

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "80144c92c53f"
down_revision: Union[str, Sequence[str], None] = "5dd1632076ed"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "validation_issues",
        sa.Column("entity_type", sa.String(length=100), nullable=True)
    )

    op.add_column(
        "validation_issues",
        sa.Column("entity_id", sa.Integer(), nullable=True)
    )

    # Existing validation issues are currently associated
    # with property units.
    op.execute("""
        UPDATE validation_issues
        SET entity_type = CASE
            WHEN property_unit_id IS NOT NULL THEN 'PROPERTY_UNIT'
            ELSE 'UNKNOWN'
        END,
        entity_id = COALESCE(property_unit_id, 0)
        WHERE entity_type IS NULL
            OR entity_id IS NULL
    """)
    # Make the new fields mandatory.
    op.alter_column(
        "validation_issues",
        "entity_type",
        existing_type=sa.String(length=100),
        nullable=False
    )

    op.alter_column(
        "validation_issues",
        "entity_id",
        existing_type=sa.Integer(),
        nullable=False
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column("validation_issues", "entity_id")
    op.drop_column("validation_issues", "entity_type")