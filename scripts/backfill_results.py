"""Idempotent conversion of recorded final requests; never fabricates history."""
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.db import get_engine
from backend.app.models import Request, ResultDocument
from backend.app.results.service import ensure_result_document


def backfill(engine=None, batch_size=100):
    engine = engine or get_engine()
    count = 0
    while True:
        with Session(engine) as db:
            ids = list(db.scalars(select(Request.id).where(Request.status.in_(['approved', 'rejected']), ~select(ResultDocument.id).where(ResultDocument.request_id == Request.id).exists()).order_by(Request.id).limit(batch_size)))
        if not ids: return count
        for request_id in ids:
            with Session(engine) as db:
                item = db.get(Request, request_id)
                if item and ensure_result_document(db, item, converted=True): count += 1
                db.commit()


if __name__ == '__main__':
    print(f'Converted final results: {backfill()}')
