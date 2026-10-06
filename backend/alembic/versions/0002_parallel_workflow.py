"""Versioned per-agency workflow tasks, routing rules and SLA snapshots."""
from alembic import op
import sqlalchemy as sa

revision='0002'
down_revision='0001'
branch_labels=None
depends_on=None


def upgrade():
    op.add_column('agencies',sa.Column('sla_days',sa.Integer,nullable=False,server_default='3'))
    op.create_table('workflow_routes',sa.Column('id',sa.Integer,primary_key=True),sa.Column('source_code',sa.String(50),sa.ForeignKey('agencies.code'),nullable=False),sa.Column('agency_id',sa.Integer,sa.ForeignKey('agencies.id'),nullable=False),sa.UniqueConstraint('source_code','agency_id',name='uq_route_destination'))
    op.create_index('ix_workflow_routes_source_code','workflow_routes',['source_code'])
    op.create_table('request_workflows',sa.Column('id',sa.Integer,primary_key=True),sa.Column('request_id',sa.Integer,sa.ForeignKey('requests.id'),nullable=False),sa.Column('agency_id',sa.Integer,sa.ForeignKey('agencies.id'),nullable=False),sa.Column('status',sa.String(20),nullable=False),sa.Column('version',sa.Integer,nullable=False),sa.Column('due_at',sa.DateTime),sa.Column('completed_at',sa.DateTime),sa.Column('decision_note',sa.Text,nullable=False),sa.Column('created_at',sa.DateTime,nullable=False),sa.Column('updated_at',sa.DateTime,nullable=False),sa.UniqueConstraint('request_id','agency_id',name='uq_request_agency'))
    for name in ['request_id','agency_id','status','due_at']:
        op.create_index('ix_request_workflows_'+name,'request_workflows',[name])
    op.execute(sa.text("""INSERT INTO request_workflows (request_id,agency_id,status,version,due_at,completed_at,decision_note,created_at,updated_at)
        SELECT id,assigned_agency_id,status,1,
        CASE WHEN status IN ('pending','processing') THEN DATE_ADD(UTC_TIMESTAMP(),INTERVAL 3 DAY) ELSE NULL END,
        CASE WHEN status IN ('approved','rejected') THEN updated_at ELSE NULL END,
        '',created_at,updated_at FROM requests
        WHERE assigned_agency_id IS NOT NULL AND status IN ('pending','processing','approved','rejected')"""))


def downgrade():
    if op.get_bind().scalar(sa.text('SELECT COUNT(*) FROM (SELECT request_id FROM request_workflows GROUP BY request_id HAVING COUNT(*)>1) AS parallel_requests')):
        raise RuntimeError('Downgrade would lose multi-agency workflow data; restore a verified backup instead.')
    op.drop_table('request_workflows')
    op.drop_table('workflow_routes')
    op.drop_column('agencies','sla_days')
