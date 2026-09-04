from alembic import op


revision = '61e5dc6be10f'
down_revision = 'a5abe6c9cf5e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        'idx_underground_assets_geometry',
        'underground_assets',
        ['geometry'],
        unique=False,
        postgresql_using='gist'
    )


def downgrade() -> None:
    op.drop_index(
        'idx_underground_assets_geometry',
        table_name='underground_assets',
        postgresql_using='gist'
    )