"""add total_billed_and_created_at_to_clients

Revision ID: 37f225f089dd
Revises: 57704372d91d
Create Date: 2025-12-23 13:42:22.063914

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '37f225f089dd'
down_revision: Union[str, Sequence[str], None] = '57704372d91d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column('clients', sa.Column('total_billed', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('clients', sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))

def downgrade():
    op.drop_column('clients', 'total_billed')
    op.drop_column('clients', 'created_at')
