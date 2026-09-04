"""update ulpins structure

Revision ID: 1b127ff72c3c
Revises: 50b676344848
Create Date: 2026-09-03 00:03:43.554012

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "1b127ff72c3c"
down_revision: Union[str, Sequence[str], None] = "50b676344848"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns with temporary defaults
    # so existing ULPIN records remain valid.

    op.add_column(
        "ulpins",
        sa.Column(
            "entity_type",
            sa.String(length=100),
            nullable=False,
            server_default="PROPERTY_UNIT"
        )
    )

    op.add_column(
        "ulpins",
        sa.Column(
            "entity_id",
            sa.Integer(),
            nullable=False,
            server_default="0"
        )
    )

    op.add_column(
        "ulpins",
        sa.Column(
            "parent_ulpin",
            sa.String(length=100),
            nullable=True
        )
    )

    op.add_column(
        "ulpins",
        sa.Column(
            "hierarchy_path",
            sa.Text(),
            nullable=True
        )
    )

    op.add_column(
        "ulpins",
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False,
            server_default="ACTIVE"
        )
    )

    # Preserve the existing relationship temporarily.
    # Copy property_unit_id into entity_id.
    op.execute(
        """
        UPDATE ulpins
        SET entity_id = property_unit_id
        """
    )

    # Remove the old foreign key.
    op.drop_constraint(
        "ulpins_property_unit_id_fkey",
        "ulpins",
        type_="foreignkey"
    )

    # Remove the old column.
    op.drop_column(
        "ulpins",
        "property_unit_id"
    )

    # Remove temporary database defaults.
    op.alter_column(
        "ulpins",
        "entity_type",
        server_default=None
    )

    op.alter_column(
        "ulpins",
        "entity_id",
        server_default=None
    )

    op.alter_column(
        "ulpins",
        "status",
        server_default=None
    )


def downgrade() -> None:

    # Re-create property_unit_id.
    op.add_column(
        "ulpins",
        sa.Column(
            "property_unit_id",
            sa.Integer(),
            nullable=True
        )
    )

    # Recover the previous relationship.
    op.execute(
        """
        UPDATE ulpins
        SET property_unit_id = entity_id
        WHERE entity_type = 'PROPERTY_UNIT'
        """
    )

    # Make it NOT NULL after restoring values.
    op.alter_column(
        "ulpins",
        "property_unit_id",
        nullable=False
    )

    # Restore foreign key.
    op.create_foreign_key(
        "ulpins_property_unit_id_fkey",
        "ulpins",
        "property_units",
        ["property_unit_id"],
        ["id"]
    )

    # Remove new columns.
    op.drop_column("ulpins", "status")
    op.drop_column("ulpins", "hierarchy_path")
    op.drop_column("ulpins", "parent_ulpin")
    op.drop_column("ulpins", "entity_id")
    op.drop_column("ulpins", "entity_type")