"""add underground asset vertical extent constraint

Revision ID: d4472b2ed692
Revises: 6844171f8656
Create Date: 2026-09-03 16:15:34.336018

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "d4472b2ed692"
down_revision: Union[str, Sequence[str], None] = "6844171f8656"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_check_constraint(
        "underground_assets_z_range_check",
        "underground_assets",
        "z_min < z_max"
    )


def downgrade() -> None:
    op.drop_constraint(
        "underground_assets_z_range_check",
        "underground_assets",
        type_="check"
    )