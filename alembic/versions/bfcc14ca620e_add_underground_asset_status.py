"""add underground asset status

Revision ID: bfcc14ca620e
Revises: d12811644f6f
Create Date: 2026-09-03 10:02:46.628283

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bfcc14ca620e'
down_revision: Union[str, Sequence[str], None] = 'd12811644f6f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        'underground_assets',
        sa.Column('status', sa.String(length=50), nullable=True)
    )

    # Give existing underground assets a default status.
    op.execute("""
        UPDATE underground_assets
        SET status = 'ACTIVE'
        WHERE status IS NULL
    """)

    # Make status mandatory.
    op.alter_column(
        'underground_assets',
        'status',
        existing_type=sa.String(length=50),
        nullable=False
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column(
        'underground_assets',
        'status'
    )