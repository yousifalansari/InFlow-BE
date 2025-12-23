"""add_company_name_to_users

Revision ID: c9b954029dc2
Revises: 37f225f089dd
Create Date: 2025-12-23 14:03:02.865694

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c9b954029dc2'
down_revision: Union[str, Sequence[str], None] = '37f225f089dd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column('users', sa.Column('company_name', sa.String(), nullable=True))

def downgrade():
    op.drop_column('users', 'company_name')