"""add validation issue status constraint

Revision ID: 57b43405d98b
Revises: 077872de08b8
Create Date: 2026-09-03 21:35:40.671843

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '57b43405d98b'
down_revision: Union[str, Sequence[str], None] = '077872de08b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_check_constraint(
        "validation_issues_status_valid",
        "validation_issues",
        "status = 'OPEN'"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "validation_issues_status_valid",
        "validation_issues",
        type_="check"
    )