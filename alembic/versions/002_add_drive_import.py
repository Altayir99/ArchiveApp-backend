"""add drive import

Revision ID: 002
Revises: 001
Create Date: 2026-05-29
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add drive_file_id to documents
    op.add_column(
        'documents',
        sa.Column('drive_file_id', sa.String(255), unique=True, nullable=True)
    )
    op.create_index('ix_documents_drive_file_id', 'documents', ['drive_file_id'])

    # Create import_jobs table
    op.create_table(
        'import_jobs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('source', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('files_found', sa.Integer, server_default='0'),
        sa.Column('files_imported', sa.Integer, server_default='0'),
        sa.Column('files_skipped', sa.Integer, server_default='0'),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('started_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('finished_at', sa.DateTime, nullable=True),
    )


def downgrade() -> None:
    op.drop_table('import_jobs')
    op.drop_index('ix_documents_drive_file_id', table_name='documents')
    op.drop_column('documents', 'drive_file_id')
