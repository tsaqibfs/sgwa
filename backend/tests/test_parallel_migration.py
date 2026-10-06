import os
import subprocess
from datetime import datetime,timedelta
import pytest
from sqlalchemy import create_engine,text
from backend.tests.safety import validated_test_url


def test_parallel_migration_preserves_existing_data():
    from backend.app.models import Base
    if not os.environ.get('TEST_DATABASE_URL'):
        pytest.skip('Test database unavailable')
    url=validated_test_url(os.environ['TEST_DATABASE_URL'])
    engine=create_engine(url)
    Base.metadata.drop_all(engine)
    with engine.begin() as c:
        c.execute(text('DROP TABLE IF EXISTS alembic_version'))
    env={**os.environ,'DATABASE_URL':url}
    def migrate(command,revision):
        return subprocess.run([os.sys.executable,'-m','alembic','-c','backend/alembic.ini',command,revision],env=env,capture_output=True,text=True)
    assert migrate('upgrade','0001').returncode==0
    with engine.begin() as c:
        c.execute(text("INSERT INTO agencies VALUES (1,'dukcapil','Dukcapil','',1)"))
        c.execute(text("INSERT INTO users VALUES (1,'Warga','warga@test.id','hash','citizen',NULL,1,UTC_TIMESTAMP())"))
        for i,status in enumerate(['pending','processing','approved','rejected','escalated'],1):
            c.execute(text("INSERT INTO requests VALUES (:id,:ref,1,'Judul','Deskripsi',1,:status,1,'2020-01-01','2020-01-02')"),{'id':i,'ref':f'OLD-{i}','status':status})
        c.execute(text("INSERT INTO request_events VALUES (1,1,1,'submitted',NULL,'pending','Riwayat lama','2020-01-01')"))
    before=datetime.utcnow()
    result=migrate('upgrade','head');assert result.returncode==0,result.stderr
    with engine.connect() as c:
        rows=c.execute(text('SELECT request_id,status,due_at FROM request_workflows ORDER BY request_id')).all()
        assert [r[1] for r in rows]==['pending','processing','approved','rejected']
        assert before+timedelta(days=3)-timedelta(seconds=2)<=rows[0][2]<=datetime.utcnow()+timedelta(days=3)
        assert c.scalar(text('SELECT note FROM request_events WHERE id=1'))=='Riwayat lama'
        assert c.scalar(text('SELECT COUNT(*) FROM requests'))==5
        assert c.scalar(text('SELECT sla_days FROM agencies WHERE id=1'))==3
    assert migrate('downgrade','0001').returncode==0
    assert migrate('upgrade','head').returncode==0
    with engine.begin() as c:
        c.execute(text("INSERT INTO agencies (id,code,name,description,active,sla_days) VALUES (2,'pajak','Pajak','',1,3)"))
        c.execute(text("INSERT INTO request_workflows (request_id,agency_id,status,version,due_at,decision_note,created_at,updated_at) VALUES (1,2,'pending',1,UTC_TIMESTAMP(),'',UTC_TIMESTAMP(),UTC_TIMESTAMP())"))
    assert migrate('downgrade','0001').returncode!=0
    Base.metadata.drop_all(engine)
    engine.dispose()
