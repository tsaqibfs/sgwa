"""Create isolated project databases against a local EnvKit root account.

Run once. Existing databases/accounts are deliberately not overwritten.
"""
import os
import secrets
from pathlib import Path
import pymysql

connection=pymysql.connect(host='127.0.0.1',port=3306,user='root',password=os.environ.get('ENVKIT_ROOT_PASSWORD',''))
with connection.cursor() as cursor:
    cursor.execute("SELECT COUNT(*) FROM mysql.user WHERE User='sgwa_demo'")
    if cursor.fetchone()[0]:
        raise SystemExit('sgwa_demo user already exists. Configure .env manually; no password was changed.')
    cursor.execute('SHOW DATABASES')
    existing={r[0] for r in cursor.fetchall()}
    if {'sgwa_demo','sgwa_test_codex'} & existing:
        raise SystemExit('Project database names already exist; choose separate names before running setup.')
    password=secrets.token_urlsafe(24)
    cursor.execute('CREATE DATABASE sgwa_demo CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci')
    cursor.execute('CREATE DATABASE sgwa_test_codex CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci')
    cursor.execute("CREATE USER 'sgwa_demo'@'127.0.0.1' IDENTIFIED BY %s",(password,))
    cursor.execute("GRANT ALL PRIVILEGES ON sgwa_demo.* TO 'sgwa_demo'@'127.0.0.1'")
    cursor.execute("GRANT ALL PRIVILEGES ON sgwa_test_codex.* TO 'sgwa_demo'@'127.0.0.1'")
connection.close()
lines=[
    f'DATABASE_URL=mysql+pymysql://sgwa_demo:{password}@127.0.0.1:3306/sgwa_demo',
    f'TEST_DATABASE_URL=mysql+pymysql://sgwa_demo:{password}@127.0.0.1:3306/sgwa_test_codex',
    'JWT_SECRET='+secrets.token_urlsafe(48),
    'TRUSTED_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173"]',
    'COOKIE_SECURE=false','MODEL_DIR=ml/artifacts','DEMO_PASSWORD='+secrets.token_urlsafe(12)
]
Path('.env').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('Project databases and local environment configured; secrets not printed.')
