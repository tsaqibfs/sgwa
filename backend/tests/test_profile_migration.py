import os
import subprocess
from sqlalchemy import create_engine, text
from backend.tests.safety import validated_test_url


def test_profile_migration_preserves_hash_and_id():
    from backend.app.models import Base
    url = validated_test_url(os.environ['TEST_DATABASE_URL'])
    engine = create_engine(url)
    Base.metadata.drop_all(engine)
    with engine.begin() as connection:
        connection.execute(text('DROP TABLE IF EXISTS alembic_version'))
    env = {**os.environ, 'DATABASE_URL': url, 'JWT_SECRET': 'test-only-secret-of-at-least-32-characters-long'}
    def migrate(revision):
        result = subprocess.run([os.sys.executable, '-m', 'alembic', '-c', 'backend/alembic.ini', 'upgrade', revision], env=env, capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
    migrate('0002')
    with engine.begin() as connection:
        connection.execute(text("INSERT INTO users (id,name,email,password_hash,role,active,created_at) VALUES (42,'Warga','migration@test.id','original-hash','citizen',1,UTC_TIMESTAMP())"))
    migrate('0003')
    with engine.connect() as connection:
        assert tuple(connection.execute(text('SELECT id,password_hash,phone,address,session_version FROM users')).one()) == (42, 'original-hash', None, None, 1)
    Base.metadata.drop_all(engine)
    engine.dispose()
