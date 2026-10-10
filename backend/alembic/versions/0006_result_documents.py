"""Immutable final decision snapshots."""
from alembic import op
import sqlalchemy as sa
revision = '0006'
down_revision = '0005'
branch_labels = depends_on = None


def upgrade():
    op.create_table('result_documents', sa.Column('id', sa.Integer, primary_key=True), sa.Column('request_id', sa.Integer, sa.ForeignKey('requests.id'), nullable=False, unique=True), sa.Column('number', sa.String(60), nullable=False, unique=True), sa.Column('snapshot', sa.JSON, nullable=False), sa.Column('created_at', sa.DateTime, nullable=False))


def downgrade():
    op.drop_table('result_documents')
