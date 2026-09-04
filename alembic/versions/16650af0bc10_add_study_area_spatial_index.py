"""add study area spatial index

Revision ID: 16650af0bc10
Revises: e75e26b6ee74
Create Date: 2026-09-02 15:17:34.930363

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '16650af0bc10'
down_revision: Union[str, Sequence[str], None] = 'e75e26b6ee74'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_index(
        'idx_study_areas_boundary',
        'study_areas',
        ['boundary'],
        unique=False,
        postgresql_using='gist'
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index(
        'idx_study_areas_boundary',
        table_name='study_areas',
        postgresql_using='gist'
    )
