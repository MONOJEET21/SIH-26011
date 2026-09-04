"""add floor vertical extent

Revision ID: 3f3527f18799
Revises: 1b127ff72c3c
Create Date: 2026-09-03 09:20:54.183642

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "3f3527f18799"
down_revision: Union[str, Sequence[str], None] = "1b127ff72c3c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    # Add temporary defaults so existing floor records
    # can receive valid vertical values.

    op.add_column(
        "floors",
        sa.Column(
            "z_min",
            sa.Float(),
            nullable=False,
            server_default="0"
        )
    )

    op.add_column(
        "floors",
        sa.Column(
            "z_max",
            sa.Float(),
            nullable=False,
            server_default="3"
        )
    )

    # Remove temporary defaults after existing records
    # have been populated.
    op.alter_column(
        "floors",
        "z_min",
        server_default=None
    )

    op.alter_column(
        "floors",
        "z_max",
        server_default=None
    )


def downgrade() -> None:

    op.drop_column(
        "floors",
        "z_max"
    )

    op.drop_column(
        "floors",
        "z_min"
    )