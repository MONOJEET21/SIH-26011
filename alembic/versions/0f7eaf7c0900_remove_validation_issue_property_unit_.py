"""remove validation issue property unit field

Revision ID: 0f7eaf7c0900
Revises: 764dadde62a9
Create Date: 2026-09-03 15:20:47.488053

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0f7eaf7c0900"
down_revision: Union[str, Sequence[str], None] = "764dadde62a9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.drop_constraint(
        "validation_issues_property_unit_id_fkey",
        "validation_issues",
        type_="foreignkey"
    )

    op.drop_column(
        "validation_issues",
        "property_unit_id"
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.add_column(
        "validation_issues",
        sa.Column(
            "property_unit_id",
            sa.Integer(),
            nullable=True
        )
    )

    op.create_foreign_key(
        "validation_issues_property_unit_id_fkey",
        "validation_issues",
        "property_units",
        ["property_unit_id"],
        ["id"]
    )