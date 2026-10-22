import os
import subprocess
import pytest
from sqlalchemy import create_engine, inspect, text
from backend.tests.safety import validated_test_url


@pytest.mark.parametrize('historical',[False,True])
def test_ml_migration_empty_and_populated_0007(historical,tmp_path):
    from backend.app.models import Base
    engine=create_engine(validated_test_url(os.environ['TEST_DATABASE_URL']))
    Base.metadata.drop_all(engine)
    with engine.begin() as db:db.execute(text('DROP TABLE IF EXISTS alembic_version'))
    env={**os.environ,'DATABASE_URL':str(engine.url.render_as_string(hide_password=False)),
         'JWT_SECRET':'migration-test-secret-at-least-32-characters','MODEL_DIR':str(tmp_path/'models')}
    def migrate(direction,revision):
        result=subprocess.run([os.sys.executable,'-m','alembic','-c','backend/alembic.ini',direction,revision],env=env,capture_output=True,text=True)
        assert result.returncode==0,result.stderr
    try:
        migrate('upgrade','0007')
        before={}
        if historical:
            with engine.begin() as db:
                db.execute(text("INSERT INTO agencies(id,code,name,description,active,sla_days) VALUES(42,'dukcapil','Dukcapil lama','',1,3)"))
                db.execute(text("INSERT INTO users(id,name,email,password_hash,role,active,created_at,session_version) VALUES(42,'Warga','old@test.id','keep-hash','citizen',1,'2026-01-01',3)"))
                db.execute(text("INSERT INTO requests(id,reference,citizen_id,title,description,status,version,created_at,updated_at) VALUES(42,'OLD-42',42,'Lama','Teks lama','approved',7,'2026-01-01','2026-01-02')"))
                db.execute(text("INSERT INTO classification_results(request_id,predicted_agency_code,probabilities,confidence,needs_review,model_version,created_at) VALUES(42,'pajak',JSON_OBJECT('pajak',1),1,0,'legacy-4','2026-01-01')"))
                db.execute(text("INSERT INTO result_documents(request_id,number,snapshot,created_at) VALUES(42,'SGWA-DEMO-OLD','{\"status\":\"approved\"}','2026-01-02')"))
            with engine.connect() as db:
                for table in ('agencies','users','requests','classification_results','result_documents'):
                    before[table]=db.execute(text(f'SELECT * FROM {table} ORDER BY id')).all()
        migrate('upgrade','head');migrate('upgrade','head')
        assert {'ml_feedback','ml_feedback_heads','ml_model_versions','ml_active_model','ml_activations'}<=set(inspect(engine).get_table_names())
        with engine.connect() as db:
            assert tuple(db.execute(text('SELECT id,model_version_id,revision FROM ml_active_model')).one())==(1,None,0)
            for table,rows in before.items():
                assert db.execute(text(f'SELECT * FROM {table} ORDER BY id')).all()==rows
        if historical:
            for _ in range(2):
                result=subprocess.run([os.sys.executable,'-m','scripts.bootstrap_ml'],env=env,capture_output=True,text=True)
                assert result.returncode==0,result.stderr
            with engine.connect() as db:
                assert db.scalar(text('SELECT revision FROM ml_active_model WHERE id=1'))==1
                for table,rows in before.items():assert db.execute(text(f'SELECT * FROM {table} ORDER BY id')).all()==rows
        migrate('downgrade','0007')
        assert 'ml_feedback' not in inspect(engine).get_table_names()
        with engine.connect() as db:
            for table,rows in before.items():assert db.execute(text(f'SELECT * FROM {table} ORDER BY id')).all()==rows
    finally:
        Base.metadata.drop_all(engine)
        with engine.begin() as db:db.execute(text('DROP TABLE IF EXISTS alembic_version'))
        engine.dispose()
