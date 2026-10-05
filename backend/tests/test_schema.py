import importlib.util
import os
import subprocess
from pathlib import Path


def test_schema_supports_new_agency():
    assert importlib.util.find_spec('backend.app.models'), 'Database models not implemented'
    from backend.app.models import Agency, Base
    from sqlalchemy import create_engine, select, func
    from sqlalchemy.orm import Session
    from sqlalchemy.exc import IntegrityError
    import pytest
    if not os.environ.get('TEST_DATABASE_URL'):
        pytest.skip('MySQL test connection not configured')
    engine = create_engine(os.environ['TEST_DATABASE_URL'])
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        db.add_all([Agency(code=c, name=c) for c in ['dukcapil','perizinan','pajak','kesehatan','pendidikan']])
        db.commit()
        assert db.scalar(select(func.count()).select_from(Agency)) == 5
        db.add(Agency(code='pendidikan', name='Duplikat'))
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()
    Base.metadata.drop_all(engine)


def test_initial_migration_upgrade_downgrade():
    config = Path('backend/alembic.ini')
    assert config.exists(), 'Alembic migration not implemented'
    if not os.environ.get('TEST_DATABASE_URL'):
        import pytest
        pytest.skip('MySQL test connection not configured')
    from sqlalchemy import create_engine, inspect, text
    env = {**os.environ, 'DATABASE_URL': os.environ['TEST_DATABASE_URL']}
    assert env['DATABASE_URL'].rsplit('/',1)[-1].startswith('sgwa_test')
    # ORM tests drop domain tables, so remove their stale migration marker too.
    with create_engine(env['DATABASE_URL']).begin() as connection:
        connection.execute(text('DROP TABLE IF EXISTS alembic_version'))
    for command in ['upgrade', 'downgrade', 'upgrade']:
        result = subprocess.run([os.sys.executable, '-m', 'alembic', '-c', str(config), command, 'base' if command == 'downgrade' else 'head'], env=env, capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        tables = inspect(create_engine(env['DATABASE_URL'])).get_table_names()
        assert ('requests' in tables) == (command == 'upgrade')
    engine = create_engine(env['DATABASE_URL'])
    assert set(inspect(engine).get_table_names()) >= {'users','agencies','requests','classification_results','request_events','audit_logs'}
    assert len(inspect(engine).get_foreign_keys('requests')) == 2
