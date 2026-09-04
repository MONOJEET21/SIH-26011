from alembic import op
import sqlalchemy as sa


revision = '50b676344848'
down_revision = '858dc32935b1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'validation_issues',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('property_unit_id', sa.Integer(), nullable=True),
        sa.Column('issue_type', sa.String(length=100), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('severity', sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(
            ['property_unit_id'],
            ['property_units.id']
        ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('validation_issues')