"""1 migrations

Revision ID: 3a10aeca20e5
Revises: f901d287972b
Create Date: 2023-10-24 18:03:15.893975

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3a10aeca20e5'
down_revision: Union[str, None] = 'f901d287972b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('products', sa.Column('unit_id', sa.Integer(), nullable=True))
    op.drop_constraint('products_unit_fkey', 'products', type_='foreignkey')
    op.create_foreign_key(None, 'products', 'units', ['unit_id'], ['id'])
    op.drop_column('products', 'unit')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('products', sa.Column('unit', sa.INTEGER(), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'products', type_='foreignkey')
    op.create_foreign_key('products_unit_fkey', 'products', 'units', ['unit'], ['id'])
    op.drop_column('products', 'unit_id')
    # ### end Alembic commands ###
