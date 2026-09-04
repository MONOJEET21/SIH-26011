from alembic import op

revision = 'e77c98b9fca4'
down_revision = 'c909ce338982'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        'idx_parcels_geometry',
        'parcels',
        ['geometry'],
        unique=False,
        postgresql_using='gist'
    )


def downgrade() -> None:
    op.drop_index(
        'idx_parcels_geometry',
        table_name='parcels',
        postgresql_using='gist'
    )