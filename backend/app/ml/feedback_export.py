"""Verified-only snapshots and connected-family grouping; no model self-labels."""
from sqlalchemy import select
from backend.app.models import MLFeedback,MLFeedbackHead
from ml.build_dataset import canonical_hash
from ml.text import text_hash


def snapshot_feedback(db) -> dict:
    rows=db.scalars(select(MLFeedback).join(MLFeedbackHead,MLFeedbackHead.current_feedback_id==MLFeedback.id)
        .where(MLFeedback.status=='verified',MLFeedbackHead.revision==MLFeedback.revision)
        .order_by(MLFeedback.request_id,MLFeedback.revision)).all()
    entries=[{key:getattr(row,key) for key in ('id','request_id','revision','training_text','corrected_code','provenance','family_key')} for row in rows]
    return {'entries':entries,'snapshot_hash':canonical_hash(entries)}


def merge_feedback(base_rows: list[dict],holdout: dict,snapshot: dict) -> tuple[list[dict],dict]:
    from backend.app.agencies.catalog import AGENCIES
    labels={code for code,_ in AGENCIES}
    entries=snapshot['entries']
    if canonical_hash(entries)!=snapshot['snapshot_hash']:raise ValueError('Snapshot feedback diubah')
    base_hash={text_hash(row['text']):row for row in base_rows}
    parent=list(range(len(entries)));links={}
    def find(n):
        while parent[n]!=n:
            parent[n]=parent[parent[n]];n=parent[n]
        return n
    def union(a,b):parent[find(b)]=find(a)
    for i,row in enumerate(entries):
        if row['corrected_code'] not in labels or row['provenance'] not in ('synthetic_demo','real'):
            raise ValueError('Label atau provenance feedback tidak valid')
        digest=text_hash(row['training_text'])
        keys=[('request',row['request_id']),('hash',digest)]
        if row.get('family_key'):keys.append(('family',row['family_key']))
        if digest in base_hash:
            base=base_hash[digest]
            if row['corrected_code']!=base['label']:raise ValueError(f'Konflik label feedback {row["id"]} dengan dataset dasar')
            keys.append(('base',base['group_id']))
        for key in keys:
            if key in links:union(i,links[key])
            else:links[key]=i
    components={}
    for i in range(len(entries)):components.setdefault(find(i),[]).append(entries[i])
    rows=[dict(row) for row in base_rows];seen=set(base_hash)
    manifest={'included':[],'excluded':[],'groups':{},'snapshot_hash':snapshot['snapshot_hash']}
    for family in components.values():
        if len({row['corrected_code'] for row in family})!=1:
            raise ValueError('Konflik label dalam keluarga feedback: '+','.join(str(row['id']) for row in family))
        base_groups={base_hash[text_hash(row['training_text'])]['group_id'] for row in family if text_hash(row['training_text']) in base_hash}
        if base_groups & set(holdout['groups']):
            manifest['excluded'].extend({'id':row['id'],'revision':row['revision'],'reason':'holdout_overlap'} for row in family)
            continue
        if len(base_groups)>1:raise ValueError('Keluarga feedback menghubungkan beberapa kelompok dasar')
        group=next(iter(base_groups)) if base_groups else 'feedback-'+canonical_hash(sorted(row['request_id'] for row in family))[:24]
        manifest['groups'][group]=[row['id'] for row in family]
        for row in family:
            digest=text_hash(row['training_text'])
            if digest in seen:
                manifest['excluded'].append({'id':row['id'],'revision':row['revision'],'reason':'duplicate'});continue
            seen.add(digest)
            rows.append(dict(text=row['training_text'],label=row['corrected_code'],group_id=group,provenance=row['provenance'],dataset_version='feedback-v1',text_hash=digest))
            manifest['included'].append({'id':row['id'],'revision':row['revision'],'group_id':group,'provenance':row['provenance']})
    return rows,manifest
