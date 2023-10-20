"""1 migrations

Revision ID: 2e515e834391
Revises: ba95c634a771
Create Date: 2023-10-20 18:26:14.820462

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2e515e834391'
down_revision: Union[str, None] = 'ba95c634a771'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('categories', 'name_rus',
               existing_type=sa.VARCHAR(),
               nullable=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('categories', 'name_rus',
               existing_type=sa.VARCHAR(),
               nullable=False)
    # ### end Alembic commands ###
