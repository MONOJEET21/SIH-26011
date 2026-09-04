from alembic import op


revision = '49eddfa177a2'
down_revision = '53db558e4c98'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        'idx_property_units_geometry',
        'property_units',
        ['geometry'],
        unique=False,
        postgresql_using='gist'
    )


def downgrade() -> None:
    op.drop_index(
        'idx_property_units_geometry',
        table_name='property_units',
        postgresql_using='gist'
    )