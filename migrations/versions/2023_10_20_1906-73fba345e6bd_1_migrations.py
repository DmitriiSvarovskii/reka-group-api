"""1 migrations

Revision ID: 73fba345e6bd
Revises: 2e515e834391
Create Date: 2023-10-20 19:06:45.366702

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '73fba345e6bd'
down_revision: Union[str, None] = '2e515e834391'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('products', 'image')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('products', sa.Column('image', sa.VARCHAR(), autoincrement=False, nullable=False))
    # ### end Alembic commands ###