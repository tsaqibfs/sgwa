"""python -m backend.app.sla.worker [--once]"""
import argparse
import time
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from backend.app.db import get_engine
from backend.app.models import utcnow
from backend.app.sla.service import escalate_overdue


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--once',action='store_true');args=parser.parse_args()
    while True:
        try:
            with Session(get_engine(),expire_on_commit=False) as db:
                count=escalate_overdue(db,utcnow())
            print(f'SLA check: {count} request(s) escalated.',flush=True)
        except SQLAlchemyError:
            print('SLA check failed: database unavailable; retry on next interval.',flush=True)
            if args.once:raise SystemExit(1)
        if args.once:return
        time.sleep(60)


if __name__=='__main__':main()
