"""rename floor number to level number

Revision ID: d7a85e1ea9f4
Revises: c00d189bb8fd
Create Date: 2026-09-03 16:00:00.359466

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "d7a85e1ea9f4"
down_revision: Union[str, Sequence[str], None] = "c00d189bb8fd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Rename floor_number to level_number."""
    op.alter_column(
        "floors",
        "floor_number",
        new_column_name="level_number"
    )


def downgrade() -> None:
    """Rename level_number back to floor_number."""
    op.alter_column(
        "floors",
        "level_number",
        new_column_name="floor_number"
    )