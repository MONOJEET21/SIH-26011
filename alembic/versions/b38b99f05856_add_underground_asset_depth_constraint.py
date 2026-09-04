"""add underground asset depth constraint

Revision ID: b38b99f05856
Revises: 7d92aa9f886b
Create Date: 2026-09-03 21:29:26.523170

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b38b99f05856'
down_revision: Union[str, Sequence[str], None] = '7d92aa9f886b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_check_constraint(
        "underground_assets_depth_non_negative",
        "underground_assets",
        "depth >= 0"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "underground_assets_depth_non_negative",
        "underground_assets",
        type_="check"
    )