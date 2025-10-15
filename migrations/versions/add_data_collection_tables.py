"""add data collection tables

Revision ID: add_data_collection_001
Revises: 
Create Date: 2025-01-15

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_data_collection_001'
down_revision = None  # Update this with your latest revision ID
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create data_collection_configs table
    op.create_table(
        'data_collection_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('exchange', sa.String(length=20), nullable=False),
        sa.Column('timeframes', sa.JSON(), nullable=False),
        sa.Column('interval_minutes', sa.Integer(), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=True),
        sa.Column('job_id', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('description', sa.String(length=200), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_data_collection_configs_enabled'), 'data_collection_configs', ['enabled'], unique=False)
    op.create_index(op.f('ix_data_collection_configs_id'), 'data_collection_configs', ['id'], unique=False)
    op.create_index(op.f('ix_data_collection_configs_symbol'), 'data_collection_configs', ['symbol'], unique=False)
    op.create_index(op.f('ix_data_collection_configs_job_id'), 'data_collection_configs', ['job_id'], unique=True)

    # Create job_execution_logs table
    op.create_table(
        'job_execution_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_name', sa.String(length=100), nullable=False),
        sa.Column('job_type', sa.String(length=50), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=True),
        sa.Column('exchange', sa.String(length=20), nullable=True),
        sa.Column('timeframe', sa.String(length=10), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('records_collected', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_type', sa.String(length=100), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_job_execution_logs_id'), 'job_execution_logs', ['id'], unique=False)
    op.create_index(op.f('ix_job_execution_logs_job_name'), 'job_execution_logs', ['job_name'], unique=False)
    op.create_index(op.f('ix_job_execution_logs_job_type'), 'job_execution_logs', ['job_type'], unique=False)
    op.create_index(op.f('ix_job_execution_logs_symbol'), 'job_execution_logs', ['symbol'], unique=False)
    op.create_index(op.f('ix_job_execution_logs_started_at'), 'job_execution_logs', ['started_at'], unique=False)
    op.create_index(op.f('ix_job_execution_logs_status'), 'job_execution_logs', ['status'], unique=False)


def downgrade() -> None:
    # Drop job_execution_logs table
    op.drop_index(op.f('ix_job_execution_logs_status'), table_name='job_execution_logs')
    op.drop_index(op.f('ix_job_execution_logs_started_at'), table_name='job_execution_logs')
    op.drop_index(op.f('ix_job_execution_logs_symbol'), table_name='job_execution_logs')
    op.drop_index(op.f('ix_job_execution_logs_job_type'), table_name='job_execution_logs')
    op.drop_index(op.f('ix_job_execution_logs_job_name'), table_name='job_execution_logs')
    op.drop_index(op.f('ix_job_execution_logs_id'), table_name='job_execution_logs')
    op.drop_table('job_execution_logs')

    # Drop data_collection_configs table
    op.drop_index(op.f('ix_data_collection_configs_job_id'), table_name='data_collection_configs')
    op.drop_index(op.f('ix_data_collection_configs_symbol'), table_name='data_collection_configs')
    op.drop_index(op.f('ix_data_collection_configs_id'), table_name='data_collection_configs')
    op.drop_index(op.f('ix_data_collection_configs_enabled'), table_name='data_collection_configs')
    op.drop_table('data_collection_configs')

