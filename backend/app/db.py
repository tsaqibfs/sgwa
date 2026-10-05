from functools import lru_cache
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from backend.app.config import get_settings


@lru_cache
def get_engine():
    return create_engine(get_settings().database_url, pool_pre_ping=True, pool_recycle=1800)


def get_session():
    with Session(get_engine(), expire_on_commit=False) as session:
        try:
            yield session
        except Exception:
            session.rollback()
            raise
