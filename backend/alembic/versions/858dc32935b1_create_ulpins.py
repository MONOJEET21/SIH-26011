from alembic import op
import sqlalchemy as sa


revision = '858dc32935b1'
down_revision = '61e5dc6be10f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'ulpins',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('property_unit_id', sa.Integer(), nullable=False),
        sa.Column('ulpin', sa.String(length=100), nullable=False),
        sa.ForeignKeyConstraint(
            ['property_unit_id'],
            ['property_units.id']
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('ulpin')
    )


def downgrade() -> None:
    op.drop_table('ulpins')