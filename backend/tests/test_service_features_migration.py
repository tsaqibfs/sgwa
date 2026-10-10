import os
import subprocess
import pytest
from sqlalchemy import create_engine, text, inspect
from backend.tests.safety import validated_test_url


@pytest.mark.parametrize('historical', [False, True])
def test_fresh_and_upgrade_preserve_history_seed_and_backfill(historical):
    from backend.app.models import Base
    url = validated_test_url(os.environ['TEST_DATABASE_URL'])
    engine = create_engine(url)
    Base.metadata.drop_all(engine)
    with engine.begin() as db: db.execute(text('DROP TABLE IF EXISTS alembic_version'))
    env = {**os.environ, 'DATABASE_URL': url, 'JWT_SECRET': 'migration-test-secret-at-least-32-characters', 'DEMO_PASSWORD': 'MigrationDemo123!'}
    def run(*args):
        output = subprocess.run([os.sys.executable, '-m', *args], env=env, capture_output=True, text=True)
        assert output.returncode == 0, output.stderr
    try:
        if historical:
            run('alembic', '-c', 'backend/alembic.ini', 'upgrade', '0002')
            with engine.begin() as db:
                db.execute(text("INSERT INTO agencies(id,code,name,description,active,sla_days) VALUES(42,'dukcapil','Dukcapil lama','',1,3)"))
                db.execute(text("INSERT INTO users(id,name,email,password_hash,role,active,created_at) VALUES(42,'Warga lama','warga@demo.sgwa.id','keep-hash','citizen',1,'2026-01-01')"))
                db.execute(text("INSERT INTO requests(id,reference,citizen_id,title,description,assigned_agency_id,status,version,created_at,updated_at) VALUES(42,'HISTORICAL-42',42,'Layanan lama','Riwayat sintetis',42,'approved',7,'2026-01-01','2026-01-02')"))
                db.execute(text("INSERT INTO request_workflows(id,request_id,agency_id,status,version,completed_at,decision_note,created_at,updated_at) VALUES(42,42,42,'approved',3,'2026-01-02','Catatan lama','2026-01-01','2026-01-02')"))
                db.execute(text("INSERT INTO audit_logs(id,actor_id,action,entity_type,entity_id,changes,created_at) VALUES(42,42,'historical','request',42,'{}','2026-01-02')"))
        run('alembic', '-c', 'backend/alembic.ini', 'upgrade', 'head')
        for _ in range(2): run('backend.app.seed'); run('scripts.backfill_results')
        with engine.connect() as db:
            assert db.scalar(text('SELECT version_num FROM alembic_version')) == '0008'
            assert db.scalar(text('SELECT COUNT(*) FROM agencies WHERE active=1')) == 25
            assert db.scalar(text('SELECT COUNT(*) FROM users')) == 5
            assert db.scalar(text('SELECT COUNT(*) FROM service_forms')) == 0
            assert db.scalar(text('SELECT COUNT(*) FROM notifications')) == 0
            assert db.scalar(text('SELECT COUNT(*) FROM mock_checks')) == 0
            if historical:
                assert tuple(db.execute(text('SELECT id,password_hash,session_version,phone,address FROM users WHERE id=42')).one()) == (42, 'keep-hash', 1, None, None)
                assert tuple(db.execute(text('SELECT id,version,form_version_id FROM requests')).one()) == (42, 7, None)
                assert tuple(db.execute(text('SELECT id,version,decision_note FROM request_workflows')).one()) == (42, 3, 'Catatan lama')
                assert db.scalar(text('SELECT action FROM audit_logs WHERE id=42')) == 'historical'
                assert db.scalar(text('SELECT COUNT(*) FROM result_documents')) == 1
                assert db.scalar(text("SELECT JSON_EXTRACT(snapshot,'$.converted') FROM result_documents")) == 'true'
            else: assert db.scalar(text('SELECT COUNT(*) FROM requests')) == 0
        assert {'service_forms','service_form_versions','notifications','result_documents','mock_checks'} <= set(inspect(engine).get_table_names())
    finally:
        Base.metadata.drop_all(engine)
        with engine.begin() as db: db.execute(text('DROP TABLE IF EXISTS alembic_version'))
        engine.dispose()
