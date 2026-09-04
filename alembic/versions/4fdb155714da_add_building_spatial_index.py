from alembic import op


revision = '4fdb155714da'
down_revision = 'ab7d57e58faa'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        'idx_buildings_geometry',
        'buildings',
        ['geometry'],
        unique=False,
        postgresql_using='gist'
    )


def downgrade() -> None:
    op.drop_index(
        'idx_buildings_geometry',
        table_name='buildings',
        postgresql_using='gist'
    )