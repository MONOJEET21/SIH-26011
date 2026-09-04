"""add floor vertical extent constraint

Revision ID: 6844171f8656
Revises: d7a85e1ea9f4
Create Date: 2026-09-03 16:11:38.565480

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "6844171f8656"
down_revision: Union[str, Sequence[str], None] = "d7a85e1ea9f4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_check_constraint(
        "floors_z_range_check",
        "floors",
        "z_min < z_max"
    )


def downgrade() -> None:
    op.drop_constraint(
        "floors_z_range_check",
        "floors",
        type_="check"
    )