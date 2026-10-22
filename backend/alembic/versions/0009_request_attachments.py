"""Request attachments per agency and supporting files."""
from alembic import op
import sqlalchemy as sa

revision = '0009'
down_revision = '0008'
branch_labels = depends_on = None


def upgrade():
    op.create_table('request_attachments',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('request_id', sa.Integer, sa.ForeignKey('requests.id'), nullable=True, index=True),
        sa.Column('agency_id', sa.Integer, sa.ForeignKey('agencies.id'), nullable=True, index=True),
        sa.Column('uploaded_by', sa.Integer, sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('stored_name', sa.String(255), nullable=False),
        sa.Column('content_type', sa.String(100), nullable=False),
        sa.Column('size_bytes', sa.Integer, nullable=False),
        sa.Column('field_key', sa.String(50), nullable=True),
        sa.Column('description', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False)
    )


def downgrade():
    op.drop_table('request_attachments')
