"""add validation issue geometry

Revision ID: ccb779460212
Revises: 400b432e610e
Create Date: 2026-09-03 15:04:03.655805

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geometry


# revision identifiers, used by Alembic.
revision: str = "ccb779460212"
down_revision: Union[str, Sequence[str], None] = "400b432e610e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "validation_issues",
        sa.Column(
            "geometry",
            Geometry(
                geometry_type="GEOMETRY",
                srid=4326,
                spatial_index=False
            ),
            nullable=True
        )
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column("validation_issues", "geometry")