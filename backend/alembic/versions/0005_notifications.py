"""Persistent transactional notifications."""
from alembic import op
import sqlalchemy as sa
revision = '0005'
down_revision = '0004'
branch_labels = depends_on = None


def upgrade():
    op.create_table('notifications', sa.Column('id', sa.Integer, primary_key=True), sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'), nullable=False), sa.Column('event_key', sa.String(150), nullable=False), sa.Column('kind', sa.String(40), nullable=False), sa.Column('title', sa.String(150), nullable=False), sa.Column('request_id', sa.Integer, sa.ForeignKey('requests.id')), sa.Column('created_at', sa.DateTime, nullable=False), sa.Column('read_at', sa.DateTime), sa.UniqueConstraint('user_id', 'event_key', name='uq_notification_event'))
    op.create_index('ix_notifications_user_id', 'notifications', ['user_id'])
    op.create_index('ix_notifications_request_id', 'notifications', ['request_id'])


def downgrade():
    op.drop_table('notifications')
