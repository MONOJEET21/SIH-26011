from alembic import op
import sqlalchemy as sa
import geoalchemy2


revision = 'a5abe6c9cf5e'
down_revision = '49eddfa177a2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'underground_assets',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('parcel_id', sa.Integer(), nullable=False),
        sa.Column('asset_type', sa.String(length=100), nullable=False),
        sa.Column(
            'geometry',
            geoalchemy2.types.Geometry(
                geometry_type='LINESTRING',
                srid=4326,
                dimension=2,
                spatial_index=False,
                from_text='ST_GeomFromEWKT',
                name='geometry',
                nullable=False
            ),
            nullable=False
        ),
        sa.ForeignKeyConstraint(
            ['parcel_id'],
            ['parcels.id']
        ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('underground_assets')