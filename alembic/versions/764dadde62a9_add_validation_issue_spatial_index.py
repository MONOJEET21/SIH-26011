"""add validation issue spatial index

Revision ID: 764dadde62a9
Revises: ccb779460212
Create Date: 2026-09-03 15:11:31.979324

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "764dadde62a9"
down_revision: Union[str, Sequence[str], None] = "ccb779460212"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_index(
        "idx_validation_issues_geometry",
        "validation_issues",
        ["geometry"],
        unique=False,
        postgresql_using="gist"
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index(
        "idx_validation_issues_geometry",
        table_name="validation_issues"
    )