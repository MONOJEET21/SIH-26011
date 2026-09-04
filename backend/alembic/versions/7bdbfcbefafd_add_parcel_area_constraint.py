"""add parcel area constraint

Revision ID: 7bdbfcbefafd
Revises: d4472b2ed692
Create Date: 2026-09-03 21:20:54.731948

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7bdbfcbefafd'
down_revision: Union[str, Sequence[str], None] = 'd4472b2ed692'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_check_constraint(
        "parcels_area_non_negative",
        "parcels",
        "area >= 0"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "parcels_area_non_negative",
        "parcels",
        type_="check"
    )