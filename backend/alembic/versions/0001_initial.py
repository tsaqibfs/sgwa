"""Initial SGWA schema."""
from alembic import op
import sqlalchemy as sa

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('agencies', sa.Column('id',sa.Integer,primary_key=True),sa.Column('code',sa.String(50),nullable=False,unique=True),sa.Column('name',sa.String(150),nullable=False),sa.Column('description',sa.Text,nullable=False),sa.Column('active',sa.Boolean,nullable=False))
    op.create_table('users',sa.Column('id',sa.Integer,primary_key=True),sa.Column('name',sa.String(150),nullable=False),sa.Column('email',sa.String(254),nullable=False,unique=True),sa.Column('password_hash',sa.String(255),nullable=False),sa.Column('role',sa.String(20),nullable=False),sa.Column('agency_id',sa.Integer,sa.ForeignKey('agencies.id')),sa.Column('active',sa.Boolean,nullable=False),sa.Column('created_at',sa.DateTime,nullable=False))
    op.create_table('requests',sa.Column('id',sa.Integer,primary_key=True),sa.Column('reference',sa.String(40),nullable=False,unique=True),sa.Column('citizen_id',sa.Integer,sa.ForeignKey('users.id'),nullable=False),sa.Column('title',sa.String(150),nullable=False),sa.Column('description',sa.Text,nullable=False),sa.Column('assigned_agency_id',sa.Integer,sa.ForeignKey('agencies.id')),sa.Column('status',sa.String(20),nullable=False),sa.Column('version',sa.Integer,nullable=False),sa.Column('created_at',sa.DateTime,nullable=False),sa.Column('updated_at',sa.DateTime,nullable=False))
    for col in ['citizen_id','assigned_agency_id','status']:
        op.create_index('ix_requests_'+col,'requests',[col])
    op.create_table('classification_results',sa.Column('id',sa.Integer,primary_key=True),sa.Column('request_id',sa.Integer,sa.ForeignKey('requests.id'),nullable=False,unique=True),sa.Column('predicted_agency_code',sa.String(50),nullable=False),sa.Column('probabilities',sa.JSON,nullable=False),sa.Column('confidence',sa.Float,nullable=False),sa.Column('needs_review',sa.Boolean,nullable=False),sa.Column('model_version',sa.String(80),nullable=False),sa.Column('created_at',sa.DateTime,nullable=False))
    op.create_table('request_events',sa.Column('id',sa.Integer,primary_key=True),sa.Column('request_id',sa.Integer,sa.ForeignKey('requests.id'),nullable=False),sa.Column('actor_id',sa.Integer,sa.ForeignKey('users.id')),sa.Column('event_type',sa.String(30),nullable=False),sa.Column('from_status',sa.String(20)),sa.Column('to_status',sa.String(20),nullable=False),sa.Column('note',sa.Text,nullable=False),sa.Column('created_at',sa.DateTime,nullable=False))
    op.create_index('ix_request_events_request_id','request_events',['request_id'])
    op.create_table('audit_logs',sa.Column('id',sa.Integer,primary_key=True),sa.Column('actor_id',sa.Integer,sa.ForeignKey('users.id')),sa.Column('action',sa.String(80),nullable=False),sa.Column('entity_type',sa.String(30),nullable=False),sa.Column('entity_id',sa.Integer,nullable=False),sa.Column('changes',sa.JSON,nullable=False),sa.Column('created_at',sa.DateTime,nullable=False))


def downgrade():
    for name in ['audit_logs','request_events','classification_results','requests','users','agencies']:
        op.drop_table(name)
