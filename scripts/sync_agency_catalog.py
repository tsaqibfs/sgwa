"""Preview catalog changes; --apply backs up MySQL before approved cleanup."""
import argparse
from datetime import datetime,timezone
from pathlib import Path
from sqlalchemy import select,text
from sqlalchemy.orm import Session
from backend.app.db import get_engine
from backend.app.models import Agency
from backend.app.agencies.catalog import AGENCIES,synchronize_catalog


def backup(engine):
    directory=Path('.superpowers/backups');directory.mkdir(parents=True,exist_ok=True)
    path=directory/('before-agency-catalog-'+datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-%f')+'.sql')
    raw=engine.raw_connection()
    try:
        connection=raw.driver_connection
        with connection.cursor() as cursor,path.open('x',encoding='utf-8') as output:
            cursor.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ')
            cursor.execute('START TRANSACTION WITH CONSISTENT SNAPSHOT')
            cursor.execute('SHOW TABLES');tables=[r[0] for r in cursor.fetchall()]
            output.write('-- Restore into a separate EMPTY schema; contains private demo data.\nSET FOREIGN_KEY_CHECKS=0;\n')
            for table in tables:
                identifier='`'+table.replace('`','``')+'`'
                cursor.execute('SHOW CREATE TABLE '+identifier);output.write(cursor.fetchone()[1]+';\n')
                cursor.execute('SELECT * FROM '+identifier)
                for row in cursor.fetchall():
                    output.write('INSERT INTO '+identifier+' VALUES ('+','.join(connection.escape(value) for value in row)+');\n')
            output.write('SET FOREIGN_KEY_CHECKS=1;\n')
        raw.rollback()
    finally:raw.close()
    return path


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    engine=get_engine()
    with engine.connect() as conn:
        version,comment=conn.execute(text('SELECT VERSION(),@@version_comment')).one()
        if 'mariadb' in (version+' '+comment).lower():raise SystemExit('Oracle MySQL diperlukan.')
        print('Engine:',version,comment)
    if args.apply:print('Backup:',backup(engine))
    with Session(engine) as db:
        try:
            counts=synchronize_catalog(db)
            print('Changes:',counts)
            if args.apply:db.commit();print('Catalog applied.')
            else:db.rollback();print('Preview only. Use --apply to commit after backup.')
        except Exception:
            db.rollback();raise
