"""Immutable published service forms and typed request answers."""
from alembic import op
import sqlalchemy as sa

revision = '0004'
down_revision = '0003'
branch_labels = depends_on = None


def upgrade():
    op.create_table('service_forms', sa.Column('id', sa.Integer, primary_key=True), sa.Column('agency_id', sa.Integer, sa.ForeignKey('agencies.id'), nullable=False), sa.Column('title', sa.String(150), nullable=False), sa.Column('active', sa.Boolean, nullable=False), sa.Column('current_version', sa.Integer, nullable=False))
    op.create_index('ix_service_forms_agency_id', 'service_forms', ['agency_id'])
    op.create_table('service_form_versions', sa.Column('id', sa.Integer, primary_key=True), sa.Column('form_id', sa.Integer, sa.ForeignKey('service_forms.id'), nullable=False), sa.Column('version', sa.Integer, nullable=False), sa.Column('title', sa.String(150), nullable=False), sa.Column('schema_json', sa.JSON, nullable=False), sa.Column('state', sa.String(20), nullable=False), sa.Column('created_by', sa.Integer, sa.ForeignKey('users.id'), nullable=False), sa.Column('created_at', sa.DateTime, nullable=False), sa.Column('published_at', sa.DateTime), sa.UniqueConstraint('form_id', 'version', name='uq_form_version'))
    op.create_index('ix_service_form_versions_form_id','service_form_versions',['form_id'])
    op.add_column('requests', sa.Column('form_version_id', sa.Integer))
    op.add_column('requests', sa.Column('form_answers', sa.JSON))
    op.create_foreign_key('fk_request_form_version','requests','service_form_versions',['form_version_id'],['id'])


def downgrade():
    op.drop_constraint('fk_request_form_version','requests',type_='foreignkey')
    op.drop_column('requests','form_answers')
    op.drop_column('requests','form_version_id')
    op.drop_table('service_form_versions')
    op.drop_table('service_forms')
