"""Add rotation chore tables

Revision ID: 20260216_rot
Revises: 8165403687aa
Create Date: 2026-02-16
"""
from alembic import op
import sqlalchemy as sa
import sqlmodel

# revision identifiers
revision = '20260216_rot'
down_revision = '8165403687aa'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'rotation_groups',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('frequency', sa.String(), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('archived', sa.Boolean(), nullable=False, server_default='0'),
    )
    
    op.create_table(
        'rotation_members',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('group_id', sa.Integer(), sa.ForeignKey('rotation_groups.id'), nullable=False),
        sa.Column('kid_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False, server_default='0'),
    )
    op.create_index('ix_rotation_members_group_id', 'rotation_members', ['group_id'])
    op.create_index('ix_rotation_members_kid_id', 'rotation_members', ['kid_id'])
    
    op.create_table(
        'rotation_logs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('group_id', sa.Integer(), sa.ForeignKey('rotation_groups.id'), nullable=False),
        sa.Column('kid_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('week_id', sa.String(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='INCOMPLETE'),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.String(), nullable=True),
    )
    op.create_index('ix_rotation_logs_group_id', 'rotation_logs', ['group_id'])
    op.create_index('ix_rotation_logs_kid_id', 'rotation_logs', ['kid_id'])
    op.create_index('ix_rotation_logs_week_id', 'rotation_logs', ['week_id'])
    op.create_index('ix_rotation_logs_date', 'rotation_logs', ['date'])
    op.create_index('ix_rotation_logs_status', 'rotation_logs', ['status'])


def downgrade() -> None:
    op.drop_table('rotation_logs')
    op.drop_table('rotation_members')
    op.drop_table('rotation_groups')
