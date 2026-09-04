"""add validation issue severity constraint

Revision ID: 077872de08b8
Revises: ca3ce62501cb
Create Date: 2026-09-03 21:33:52.435267

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '077872de08b8'
down_revision: Union[str, Sequence[str], None] = 'ca3ce62501cb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_check_constraint(
        "validation_issues_severity_valid",
        "validation_issues",
        "severity IN ('LOW', 'MEDIUM', 'HIGH')"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "validation_issues_severity_valid",
        "validation_issues",
        type_="check"
    )