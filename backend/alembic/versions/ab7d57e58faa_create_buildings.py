from alembic import op
import sqlalchemy as sa
import geoalchemy2


revision = 'ab7d57e58faa'
down_revision = 'e77c98b9fca4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'buildings',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('parcel_id', sa.Integer(), nullable=False),
        sa.Column('building_number', sa.String(length=100), nullable=False),
        sa.Column(
            'geometry',
            geoalchemy2.types.Geometry(
                geometry_type='POLYGON',
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
    op.drop_table('buildings')