from alembic import op


revision = 'f71a8dad874a'
down_revision = '3af4533d4339'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        'idx_floors_geometry',
        'floors',
        ['geometry'],
        unique=False,
        postgresql_using='gist'
    )


def downgrade() -> None:
    op.drop_index(
        'idx_floors_geometry',
        table_name='floors',
        postgresql_using='gist'
    )