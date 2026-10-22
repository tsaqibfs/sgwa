"""Verified feedback and immutable model registry; no historical data mutation."""
from alembic import op
import sqlalchemy as sa

revision='0008'
down_revision='0007'
branch_labels=depends_on=None


def upgrade():
    op.create_table('ml_feedback',
        sa.Column('id',sa.Integer,primary_key=True),
        sa.Column('request_id',sa.Integer,sa.ForeignKey('requests.id'),nullable=False),
        sa.Column('revision',sa.Integer,nullable=False),
        sa.Column('original_text',sa.Text,nullable=False),
        sa.Column('original_prediction',sa.JSON,nullable=False),
        sa.Column('training_text',sa.Text,nullable=False),
        sa.Column('text_hash',sa.String(64),nullable=False),
        sa.Column('corrected_code',sa.String(50),sa.ForeignKey('agencies.code'),nullable=False),
        sa.Column('provenance',sa.String(20),nullable=False),
        sa.Column('family_key',sa.String(80)),
        sa.Column('reason',sa.Text,nullable=False),
        sa.Column('status',sa.String(20),nullable=False),
        sa.Column('created_by',sa.Integer,sa.ForeignKey('users.id'),nullable=False),
        sa.Column('created_at',sa.DateTime,nullable=False),
        sa.Column('reviewed_by',sa.Integer,sa.ForeignKey('users.id')),
        sa.Column('reviewed_at',sa.DateTime),sa.Column('review_note',sa.Text),
        sa.Column('idempotency_key',sa.String(100),nullable=False),
        sa.Column('payload_hash',sa.String(64),nullable=False),
        sa.UniqueConstraint('request_id','revision',name='uq_ml_feedback_revision'),
        sa.UniqueConstraint('created_by','idempotency_key',name='uq_ml_feedback_key'),
        sa.CheckConstraint("status IN ('pending','verified','rejected','superseded')",name='ck_ml_feedback_status'),
        sa.CheckConstraint("provenance IN ('synthetic_demo','real')",name='ck_ml_feedback_provenance'))
    for name in ('request_id','text_hash','status'):op.create_index('ix_ml_feedback_'+name,'ml_feedback',[name])
    op.create_table('ml_feedback_heads',
        sa.Column('request_id',sa.Integer,sa.ForeignKey('requests.id'),primary_key=True),
        sa.Column('revision',sa.Integer,nullable=False),
        sa.Column('current_feedback_id',sa.Integer,sa.ForeignKey('ml_feedback.id',name='fk_ml_head_current')))
    op.create_table('ml_model_versions',
        sa.Column('id',sa.String(80),primary_key=True),sa.Column('state',sa.String(20),nullable=False),
        sa.Column('relative_path',sa.String(150),nullable=False),sa.Column('model_hash',sa.String(64),nullable=False),
        sa.Column('metadata_json',sa.JSON,nullable=False),sa.Column('evaluation_json',sa.JSON,nullable=False),
        sa.Column('feedback_manifest',sa.JSON,nullable=False),sa.Column('created_at',sa.DateTime,nullable=False),
        sa.Column('registered_by',sa.Integer,sa.ForeignKey('users.id')),sa.Column('failure_reason',sa.Text),
        sa.CheckConstraint("state IN ('ready','failed')",name='ck_ml_model_state'))
    op.create_table('ml_active_model',
        sa.Column('id',sa.Integer,primary_key=True,autoincrement=False),
        sa.Column('model_version_id',sa.String(80),sa.ForeignKey('ml_model_versions.id')),
        sa.Column('revision',sa.Integer,nullable=False),sa.CheckConstraint('id=1',name='ck_ml_singleton'))
    op.create_table('ml_activations',
        sa.Column('id',sa.Integer,primary_key=True),
        sa.Column('model_version_id',sa.String(80),sa.ForeignKey('ml_model_versions.id'),nullable=False),
        sa.Column('previous_version_id',sa.String(80),sa.ForeignKey('ml_model_versions.id')),
        sa.Column('actor_id',sa.Integer,sa.ForeignKey('users.id')),sa.Column('reason',sa.Text,nullable=False),
        sa.Column('kind',sa.String(20),nullable=False),sa.Column('created_at',sa.DateTime,nullable=False))
    op.execute('INSERT INTO ml_active_model(id,model_version_id,revision) VALUES(1,NULL,0)')


def downgrade():
    for table in ('ml_activations','ml_active_model','ml_model_versions','ml_feedback_heads','ml_feedback'):
        op.drop_table(table)
