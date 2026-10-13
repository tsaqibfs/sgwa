from collections.abc import Iterator
from sqlalchemy.orm import Session
from backend.app.db import get_engine

def get_report_session()->Iterator[Session]:
    # Auth's session may already have a transaction; leave it untouched.
    engine=get_engine().execution_options(isolation_level='REPEATABLE READ')
    with Session(engine,expire_on_commit=False) as session:
        try:yield session
        except Exception:
            session.rollback()
            raise
