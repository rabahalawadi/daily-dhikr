"""initial schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-10-19 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'source_records',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('source_type', sa.String(length=50), nullable=False),
        sa.Column('source_name', sa.String(length=255), nullable=False),
        sa.Column('reference', sa.String(length=255), nullable=False),
        sa.Column('hadith_grade', sa.String(length=100), nullable=True),
        sa.Column('grading_source', sa.String(length=255), nullable=True),
        sa.Column('verification_notes', sa.Text(), nullable=True),
        sa.Column('verified_by', sa.String(length=100), nullable=True),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_source_records_type', 'source_records', ['source_type'])
    op.create_index('ix_source_records_status', 'source_records', ['status'])

    op.create_table(
        'content_items',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('arabic_text', sa.Text(), nullable=False),
        sa.Column('english_meaning', sa.Text(), nullable=False),
        sa.Column('transliteration', sa.Text(), nullable=True),
        sa.Column('caption_ar', sa.Text(), nullable=True),
        sa.Column('caption_en', sa.Text(), nullable=True),
        sa.Column('source_id', sa.String(length=36), nullable=False),
        sa.Column('verification_status', sa.String(length=50), nullable=False),
        sa.Column('approval_status', sa.String(length=50), nullable=False),
        sa.Column('is_demo', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['source_id'], ['source_records.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_content_items_category', 'content_items', ['category'])
    op.create_index('ix_content_items_source_id', 'content_items', ['source_id'])
    op.create_index('ix_content_items_verification', 'content_items', ['verification_status'])
    op.create_index('ix_content_items_approval', 'content_items', ['approval_status'])
    op.create_index('ix_content_items_is_demo', 'content_items', ['is_demo'])

    op.create_table(
        'media_assets',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('content_id', sa.String(length=36), nullable=False),
        sa.Column('asset_type', sa.String(length=50), nullable=False),
        sa.Column('storage_url', sa.String(length=1024), nullable=False),
        sa.Column('local_path', sa.String(length=512), nullable=True),
        sa.Column('width', sa.Integer(), nullable=False),
        sa.Column('height', sa.Integer(), nullable=False),
        sa.Column('checksum', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['content_id'], ['content_items.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_media_assets_content_id', 'media_assets', ['content_id'])
    op.create_index('ix_media_assets_type', 'media_assets', ['asset_type'])
    op.create_index('ix_media_assets_checksum', 'media_assets', ['checksum'])

    op.create_table(
        'publication_jobs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('content_id', sa.String(length=36), nullable=False),
        sa.Column('platform', sa.String(length=50), nullable=False),
        sa.Column('publication_type', sa.String(length=50), nullable=False),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('attempt_count', sa.Integer(), nullable=False),
        sa.Column('instagram_media_id', sa.String(length=100), nullable=True),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('claimed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['content_id'], ['content_items.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_publication_jobs_content_id', 'publication_jobs', ['content_id'])
    op.create_index('ix_publication_jobs_type', 'publication_jobs', ['publication_type'])
    op.create_index('ix_publication_jobs_status', 'publication_jobs', ['status'])
    op.create_index('ix_publication_jobs_due', 'publication_jobs', ['status', 'scheduled_at'])

    op.create_table(
        'publication_attempts',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('job_id', sa.String(length=36), nullable=False),
        sa.Column('attempt_number', sa.Integer(), nullable=False),
        sa.Column('request_started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('response_received_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('response_status', sa.Integer(), nullable=True),
        sa.Column('error_category', sa.String(length=50), nullable=True),
        sa.Column('error_message_redacted', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['job_id'], ['publication_jobs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_publication_attempts_job_id', 'publication_attempts', ['job_id'])

    op.create_table(
        'app_settings',
        sa.Column('key', sa.String(length=100), nullable=False),
        sa.Column('value', sa.Text(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('key')
    )

    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.String(length=36), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('details', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('ix_audit_logs_entity', 'audit_logs', ['entity_type', 'entity_id'])
    op.create_index('ix_audit_logs_timestamp', 'audit_logs', ['timestamp'])


def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('app_settings')
    op.drop_table('publication_attempts')
    op.drop_table('publication_jobs')
    op.drop_table('media_assets')
    op.drop_table('content_items')
    op.drop_table('source_records')
