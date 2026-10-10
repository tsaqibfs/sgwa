"""Authenticated local simulation history."""
from alembic import op
import sqlalchemy as sa
revision = '0007'
down_revision = '0006'
branch_labels = depends_on = None


def upgrade():
    op.create_table('mock_checks', sa.Column('id', sa.Integer, primary_key=True), sa.Column('request_id', sa.Integer, sa.ForeignKey('requests.id'), nullable=False), sa.Column('actor_id', sa.Integer, sa.ForeignKey('users.id'), nullable=False), sa.Column('check_type', sa.String(40), nullable=False), sa.Column('outcome', sa.String(30), nullable=False), sa.Column('checked_at', sa.DateTime, nullable=False), sa.Column('payload', sa.JSON, nullable=False), sa.Column('idempotency_key', sa.String(100), nullable=False), sa.UniqueConstraint('actor_id', 'idempotency_key', name='uq_mock_actor_key'))
    op.create_index('ix_mock_checks_request_id', 'mock_checks', ['request_id'])


def downgrade():
    op.drop_table('mock_checks')
