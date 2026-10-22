"""Profiles and revocable session versions."""
from alembic import op
import sqlalchemy as sa

revision = '0003'
down_revision = '0002'
branch_labels = depends_on = None


def upgrade():
    op.add_column('users', sa.Column('phone', sa.String(30)))
    op.add_column('users', sa.Column('address', sa.String(500)))
    op.add_column('users', sa.Column('session_version', sa.Integer, nullable=False, server_default='1'))


def downgrade():
    for column in ('session_version', 'address', 'phone'):
        op.drop_column('users', column)
