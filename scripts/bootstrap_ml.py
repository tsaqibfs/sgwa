"""Explicit first-install bootstrap; subsequent starts preserve admin selection."""
from pathlib import Path
import shutil
import uuid
from sqlalchemy import select,text
from sqlalchemy.orm import Session
from backend.app.config import get_settings
from backend.app.db import get_engine
from backend.app.models import MLActiveModel,MLModelVersion
from backend.app.ml.registry import validated_version,activate_model
from backend.app.ml.classifier import Classifier
from scripts.train_candidate import train_candidate


def bootstrap_ml() -> dict:
    engine=get_engine()
    # Connection-scoped MySQL lock protects two simultaneous installer starts.
    lock_key='sgwa-ml-bootstrap:'+str(engine.url.database)
    with engine.connect() as connection:
        if connection.scalar(text('SELECT GET_LOCK(:name,30)'),{'name':lock_key})!=1:
            raise ValueError('Bootstrap ML sedang berjalan di proses lain')
        try:
            with Session(engine) as db:
                pointer=db.get(MLActiveModel,1)
                if pointer and pointer.model_version_id:
                    row=db.get(MLModelVersion,pointer.model_version_id)
                    try:
                        directory,_,_=validated_version(row);Classifier(directory)
                    except Exception as exc:
                        raise ValueError('Artefak model aktif tidak valid; pulihkan file atau rollback. Bootstrap tidak menggantinya.') from exc
                    return {'created':False,'model_id':row.id}
                if pointer and pointer.revision>0:
                    raise ValueError('Pointer aktif tidak konsisten; perlu pemulihan admin')
            root=get_settings().model_dir.resolve()
            legacy=[root/name for name in ('model.joblib','metadata.json','evaluation.json','train.csv','test.csv') if (root/name).is_file()]
            if legacy:
                archive=root/'archive'/('legacy-'+uuid.uuid4().hex);archive.mkdir(parents=True)
                for file in legacy:shutil.copy2(file,archive/file.name)
            model_id=train_candidate(None,bootstrap=True)
            with Session(engine) as db:
                activate_model(db,None,model_id,0,'Bootstrap awal model 25 kelas, holdout sintetis.','bootstrap')
            return {'created':True,'model_id':model_id}
        finally:
            connection.execute(text('SELECT RELEASE_LOCK(:name)'),{'name':lock_key})


if __name__=='__main__':
    result=bootstrap_ml()
    print(('Bootstrap model25 selesai: ' if result['created'] else 'Model aktif dipertahankan: ')+result['model_id'])
