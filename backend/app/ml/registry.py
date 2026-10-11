"""Register trusted content-addressed artifacts; activation is a separate action."""
import json
import math
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.dialects.mysql import insert
from fastapi import HTTPException
from backend.app.config import get_settings
from backend.app.models import MLModelVersion,MLActiveModel,MLActivation
from backend.app.audit.service import record
from backend.app.ml.feedback import locked_admin
from ml.train import validate_artifacts


def artifact_directory(version) -> Path:
    root=get_settings().model_dir.resolve()
    directory=(root/version.relative_path).resolve()
    if directory!=root/'versions'/version.id or not directory.is_relative_to(root/'versions'):
        raise ValueError('Lokasi model tidak valid')
    return directory


def register_candidate(db,directory: Path,actor_id: int|None) -> MLModelVersion:
    info=validate_artifacts(directory)
    root=get_settings().model_dir.resolve()
    if directory.resolve()!=root/'versions'/info['model_version']:
        raise ValueError('Kandidat harus berada di direktori versi model')
    report=json.loads((directory/'evaluation.json').read_text(encoding='utf-8'))
    manifest=json.loads((directory/'manifest.json').read_text(encoding='utf-8'))['feedback']
    existing=db.get(MLModelVersion,info['model_version'])
    if existing:
        if existing.state!='ready' or not json_equivalent(existing.metadata_json,info) or existing.feedback_manifest!=manifest:
            raise ValueError('Versi model sudah terdaftar dengan artefak berbeda')
        return existing
    row=MLModelVersion(id=info['model_version'],state='ready',relative_path='versions/'+info['model_version'],model_hash=info['model_hash'],
                       metadata_json=info,evaluation_json=report,feedback_manifest=manifest,registered_by=actor_id)
    db.add(row);db.flush();return row


def validated_version(row):
    if not row or row.state!='ready':raise ValueError('Versi model belum siap')
    directory=artifact_directory(row)
    info=validate_artifacts(directory)
    report=json.loads((directory/'evaluation.json').read_text(encoding='utf-8'))
    if not json_equivalent(row.metadata_json,info) or not json_equivalent(row.evaluation_json,report) or row.model_hash!=info['model_hash']:
        raise ValueError('Registry dan artefak tidak cocok')
    return directory,info,report


def json_equivalent(left,right):
    """MySQL binary JSON may round the final double digit; hashes stay exact."""
    if type(left) is not type(right):return False
    if isinstance(left,dict):return left.keys()==right.keys() and all(json_equivalent(left[k],right[k]) for k in left)
    if isinstance(left,list):return len(left)==len(right) and all(json_equivalent(a,b) for a,b in zip(left,right))
    if isinstance(left,float):return math.isfinite(left) and math.isfinite(right) and math.isclose(left,right,rel_tol=0,abs_tol=1e-15)
    return left==right


def check_activation(active: dict|None,candidate: dict,kind: str,previously_active: bool) -> None:
    if kind not in ('activate','rollback','bootstrap'):raise HTTPException(422,'Jenis aktivasi tidak valid.')
    if kind=='rollback' and not previously_active:raise HTTPException(422,'Rollback hanya untuk versi yang pernah aktif.')
    if active:
        if active['holdout_manifest_hash']!=candidate['holdout_manifest_hash']:
            raise HTTPException(422,'Generasi holdout berbeda; evaluasi tidak sebanding.')
        if kind=='activate' and candidate['macro_f1']+0.02+1e-12<active['macro_f1']:
            raise HTTPException(422,'Macro-F1 turun lebih dari 0,02; kandidat tidak dapat diaktifkan.')


def activate_model(db,actor,model_id: str,expected_revision: int,reason: str,kind: str='activate') -> dict:
    if actor is not None:actor=locked_admin(db,actor)
    elif kind!='bootstrap':raise HTTPException(403,'Aktivasi memerlukan admin.')
    statement=insert(MLActiveModel).values(id=1,revision=0,model_version_id=None)
    db.execute(statement.on_duplicate_key_update(id=1))
    pointer=db.scalar(select(MLActiveModel).where(MLActiveModel.id==1).with_for_update().execution_options(populate_existing=True))
    if pointer.revision!=expected_revision:raise HTTPException(409,'Model aktif telah berubah. Muat ulang versinya.')
    row=db.get(MLModelVersion,model_id)
    if not row:raise HTTPException(404,'Versi model tidak ditemukan.')
    try:directory,info,report=validated_version(row)
    except (ValueError,OSError,KeyError,TypeError) as exc:raise HTTPException(422,'Artefak kandidat tidak valid.') from exc
    # Deserialize and validate actual estimator classes before publishing pointer.
    from backend.app.ml.classifier import Classifier,ModelUnavailable
    try:Classifier(directory)
    except ModelUnavailable as exc:raise HTTPException(422,'Estimator kandidat tidak valid.') from exc
    previous=db.get(MLModelVersion,pointer.model_version_id) if pointer.model_version_id else None
    prior_report=previous.evaluation_json if previous else None
    seen=db.scalar(select(MLActivation.id).where(MLActivation.model_version_id==model_id).limit(1)) is not None
    if kind=='bootstrap' and pointer.model_version_id:raise HTTPException(409,'Model sudah aktif; bootstrap tidak menggantinya.')
    check_activation(prior_report,report,kind,seen)
    old_id=pointer.model_version_id
    if old_id==model_id:return {'active_model_id':model_id,'revision':pointer.revision}
    pointer.model_version_id=model_id;pointer.revision+=1
    db.add(MLActivation(model_version_id=model_id,previous_version_id=old_id,actor_id=actor.id if actor else None,reason=reason,kind=kind))
    record(db,actor.id if actor else None,'ml.model_'+kind,'ml_model',0,{'model_id':model_id,'previous_model_id':old_id,'revision':pointer.revision,'reason':reason})
    db.commit();return {'active_model_id':model_id,'revision':pointer.revision}
