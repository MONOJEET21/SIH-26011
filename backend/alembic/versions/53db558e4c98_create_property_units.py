from alembic import op
import sqlalchemy as sa
import geoalchemy2


revision = '53db558e4c98'
down_revision = 'f71a8dad874a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'property_units',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('floor_id', sa.Integer(), nullable=False),
        sa.Column('unit_number', sa.String(length=100), nullable=False),
        sa.Column('unit_type', sa.String(length=100), nullable=False),
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
            ['floor_id'],
            ['floors.id']
        ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('property_units')