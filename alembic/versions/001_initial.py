""initial schema

Revision ID: 001
Revises:
Create Date: 2026-05-28
""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, TSVECTOR

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        'workspaces',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('initials', sa.String(4), nullable=False),
        sa.Column('color', sa.String(7), nullable=False),
        sa.Column('text_color', sa.String(7), nullable=False),
        sa.Column('owner_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        'documents',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('workspace_id', UUID(as_uuid=True), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('file_type', sa.String(10), nullable=False),
        sa.Column('source', sa.String(50), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('summary', sa.Text, nullable=True),
        sa.Column('file_path', sa.String(500), nullable=True),
        sa.Column('file_size', sa.BigInteger, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('search_vector', TSVECTOR, nullable=True),
    )

    op.create_index('idx_documents_search', 'documents', ['search_vector'], postgresql_using='gin')

    op.execute('''
        CREATE OR REPLACE FUNCTION update_search_vector()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.search_vector :=
                setweight(to_tsvector('german', COALESCE(NEW.title, '')), 'A') ||
                setweight(to_tsvector('german', COALESCE(NEW.summary, '')), 'B') ||
                setweight(to_tsvector('german', COALESCE(NEW.category, '')), 'C');
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    ''')

    op.execute('''
        CREATE TRIGGER trg_update_search_vector
        BEFORE INSERT OR UPDATE ON documents
        FOR EACH ROW
        EXECUTE FUNCTION update_search_vector();
    ''')


def downgrade() -> None:
    op.execute('DROP TRIGGER IF EXISTS trg_update_search_vector ON documents')
    op.execute('DROP FUNCTION IF EXISTS update_search_vector()')
    op.drop_index('idx_documents_search')
    op.drop_table('documents')
    op.drop_table('workspaces')
    op.drop_table('users')
