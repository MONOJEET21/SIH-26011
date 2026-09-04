from alembic import op
import sqlalchemy as sa
import geoalchemy2


revision = '3af4533d4339'
down_revision = '4fdb155714da'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'floors',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('building_id', sa.Integer(), nullable=False),
        sa.Column('floor_number', sa.Integer(), nullable=False),
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
            ['building_id'],
            ['buildings.id']
        ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('floors')