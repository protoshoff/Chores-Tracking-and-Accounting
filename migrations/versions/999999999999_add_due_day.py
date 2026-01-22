"""add due_day to chores

Revision ID: 999999999999
Revises: 8165403687aa
Create Date: 2026-01-22 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel

# revision identifiers, used by Alembic.
revision = '999999999999'
down_revision = '8165403687aa'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add due_day column to chores table
    op.add_column('chores', sa.Column('due_day', sa.Integer(), nullable=True))


def downgrade() -> None:
    # Remove due_day column
    op.drop_column('chores', 'due_day')
