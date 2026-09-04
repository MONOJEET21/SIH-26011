"""add ulpin entity type constraint

Revision ID: ca3ce62501cb
Revises: b38b99f05856
Create Date: 2026-09-03 21:31:45.041393

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ca3ce62501cb'
down_revision: Union[str, Sequence[str], None] = 'b38b99f05856'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_check_constraint(
        "ulpins_entity_type_valid",
        "ulpins",
        "entity_type IN ('STUDY_AREA', 'PARCEL', 'BUILDING', 'FLOOR', 'PROPERTY_UNIT')"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "ulpins_entity_type_valid",
        "ulpins",
        type_="check"
    )