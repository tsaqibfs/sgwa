"""Operator batch training. This command never activates its candidate."""
import argparse
import csv
import json
from pathlib import Path
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.config import get_settings
from backend.app.db import get_engine
from backend.app.models import User,MLModelVersion
from backend.app.audit.service import record
from backend.app.ml.feedback_export import snapshot_feedback,merge_feedback
from backend.app.ml.registry import register_candidate
from ml.build_dataset import FIELDS,canonical_hash
from ml.train import train,validate_artifacts


def train_candidate(actor_email: str|None, *, bootstrap: bool=False) -> str:
    settings=get_settings();root=settings.model_dir.resolve();actor_id=None
    with Session(get_engine()) as db:
        if not bootstrap:
            actor=db.scalar(select(User).where(User.email==actor_email,User.role=='admin',User.active.is_(True)))
            if not actor:raise ValueError('Operator harus memilih akun admin aktif')
            actor_id=actor.id
        snapshot={'entries':[],'snapshot_hash':canonical_hash([])} if bootstrap else snapshot_feedback(db)
    staging=root/'.staging'/uuid.uuid4().hex;staging.mkdir(parents=True)
    try:
        with Path('ml/data/requests.csv').open(encoding='utf-8') as f:base=list(csv.DictReader(f))
        holdout=json.loads(Path('ml/data/holdout.json').read_text())
        rows,manifest=merge_feedback(base,holdout,snapshot)
        path=staging/'dataset.csv'
        with path.open('w',encoding='utf-8',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=FIELDS);writer.writeheader();writer.writerows(rows)
        report=train(path,staging,holdout_path=Path('ml/data/holdout.json'),feedback_manifest=manifest)
        info=validate_artifacts(staging)
        destination=root/'versions'/report['model_version'];destination.parent.mkdir(parents=True,exist_ok=True)
        if destination.exists():
            if validate_artifacts(destination)!=info:raise ValueError('Identitas versi bertabrakan dengan artefak berbeda')
        else:staging.rename(destination)
        with Session(get_engine()) as db:
            row=register_candidate(db,destination,actor_id)
            record(db,actor_id,'ml.candidate_registered','ml_model',0,{'model_id':row.id,'snapshot_hash':snapshot['snapshot_hash']})
            db.commit()
        return report['model_version']
    except Exception as exc:
        with Session(get_engine()) as db:
            failed_id='failed-'+uuid.uuid4().hex
            db.add(MLModelVersion(id=failed_id,state='failed',relative_path='',model_hash='',metadata_json={},evaluation_json={},
                                 feedback_manifest={'snapshot_hash':snapshot['snapshot_hash']},registered_by=actor_id,failure_reason=type(exc).__name__+': '+str(exc)[:500]))
            db.commit()
        raise


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--actor-email',required=True);args=parser.parse_args()
    model_id=train_candidate(args.actor_email)
    print('Kandidat siap: '+model_id+'. Review evaluasi lalu aktifkan melalui halaman Model ML; model aktif belum diubah.')
