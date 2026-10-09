"""User-approved agency catalog; codes stay stable for existing ML labels."""
import re
from sqlalchemy import select,delete,update,or_
from sqlalchemy.orm import Session
from backend.app.models import Agency,User,Request,RequestWorkflow,WorkflowRoute,RequestEvent,ClassificationResult,AuditLog
from backend.app.audit.service import record

AGENCIES=(
 ('kearsipan_perpustakaan','DINAS KEARSIPAN DAN PERPUSTAKAAN DAERAH'),
 ('dukcapil','DINAS KEPENDUDUKAN DAN PENCATATAN SIPIL'),
 ('kesehatan','DINAS KESEHATAN'),
 ('pangan_pertanian','DINAS KETAHANAN PANGAN DAN PERTANIAN'),
 ('kominfo','DINAS KOMUNIKASI DAN INFORMATIKA'),
 ('koperasi_usaha_mikro','DINAS KOPERASI DAN USAHA MIKRO'),
 ('lingkungan_hidup','DINAS LINGKUNGAN HIDUP'),
 ('pariwisata_kebudayaan','DINAS PARIWISATA DAN KEBUDAYAAN'),
 ('pu_bina_marga','DINAS PEKERJAAN UMUM BINA MARGA'),
 ('pu_sumber_daya_air','DINAS PEKERJAAN UMUM SUMBER DAYA AIR'),
 ('pemberdayaan_desa','DINAS PEMBERDAYAAN MASYARAKAT DAN DESA'),
 ('pemberdayaan_perempuan_anak','DINAS PEMBERDAYAAN PEREMPUAN DAN PERLINDUNGAN ANAK'),
 ('pemuda_olahraga','DINAS PEMUDA DAN OLAHRAGA'),
 ('perizinan','DINAS PENANAMAN MODAL DAN PELAYANAN TERPADU SATU PINTU'),
 ('pendidikan','DINAS PENDIDIKAN'),
 ('pengendalian_penduduk_kb','DINAS PENGENDALIAN PENDUDUK DAN KELUARGA BERENCANA'),
 ('perhubungan','DINAS PERHUBUNGAN'),
 ('perikanan','DINAS PERIKANAN'),
 ('perindustrian_perdagangan','DINAS PERINDUSTRIAN DAN PERDAGANGAN'),
 ('perumahan_permukiman_cipta_karya','DINAS PERUMAHAN RAKYAT, KAWASAN PERMUKIMAN DAN CIPTA KARYA'),
 ('peternakan_kesehatan_hewan','DINAS PETERNAKAN DAN KESEHATAN HEWAN'),
 ('sosial','DINAS SOSIAL'),
 ('tenaga_kerja','DINAS TENAGA KERJA'),
 ('bpbd','BADAN PENANGGULANGAN BENCANA DAERAH'),
 ('satpol_pp','SATUAN POLISI PAMONG PRAJA'),
)


def upsert_catalog(db:Session):
    existing={a.code:a for a in db.scalars(select(Agency).order_by(Agency.id).with_for_update())}
    added=renamed=0
    for code,name in AGENCIES:
        agency=existing.get(code)
        if agency:
            if agency.name!=name:agency.name=name;renamed+=1
        else:
            db.add(Agency(code=code,name=name));added+=1
    db.flush()
    return {'added_agencies':added,'renamed_agencies':renamed}


def synchronize_catalog(db:Session):
    """Caller owns commit/rollback. Delete only recognized retired demo agencies."""
    agencies=db.scalars(select(Agency).order_by(Agency.id).with_for_update()).all()
    retired=[a for a in agencies if a.code=='pajak' and a.name in ('Badan Pendapatan Daerah','BADAN PENDAPATAN DAERAH') or re.fullmatch(r'pendidikan_\d+',a.code) and a.name.startswith('Dinas Pendidikan Demo ')]
    ids=[a.id for a in retired];codes=[a.code for a in retired]
    staff=db.scalars(select(User).where(User.agency_id.in_(ids)).with_for_update()).all() if ids else []
    if any(u.role!='staff' or not u.email.endswith('@demo.sgwa.id') for u in staff):
        raise ValueError('Ada akun non-demo terkait instansi lama; pembersihan dibatalkan.')
    request_ids=set(db.scalars(select(RequestWorkflow.request_id).where(RequestWorkflow.agency_id.in_(ids)))) if ids else set()
    requests=db.scalars(select(Request).where(or_(Request.assigned_agency_id.in_(ids),Request.id.in_(request_ids))).with_for_update()).all() if ids else []
    for item in requests:
        owner=db.get(User,item.citizen_id)
        if not owner or owner.email!='warga@demo.sgwa.id':
            raise ValueError('Ada pengajuan non-demo terkait instansi lama; pembersihan dibatalkan.')
    request_ids=[r.id for r in requests];staff_ids=[u.id for u in staff]
    if request_ids:
        for model in (RequestWorkflow,RequestEvent,ClassificationResult):
            db.execute(delete(model).where(model.request_id.in_(request_ids)))
        db.execute(delete(AuditLog).where(AuditLog.entity_type=='request',AuditLog.entity_id.in_(request_ids)))
        db.execute(delete(Request).where(Request.id.in_(request_ids)))
    if staff_ids:
        # Keep unrelated history valid even if a retired demo actor authored it.
        db.execute(update(RequestEvent).where(RequestEvent.actor_id.in_(staff_ids)).values(actor_id=None))
        db.execute(update(AuditLog).where(AuditLog.actor_id.in_(staff_ids)).values(actor_id=None))
        db.execute(delete(User).where(User.id.in_(staff_ids)))
    if ids:
        db.execute(delete(WorkflowRoute).where(or_(WorkflowRoute.agency_id.in_(ids),WorkflowRoute.source_code.in_(codes))))
        db.execute(delete(Agency).where(Agency.id.in_(ids)))
    counts={**upsert_catalog(db),'removed_agencies':len(ids),'removed_requests':len(request_ids),'removed_staff':len(staff_ids)}
    record(db,None,'agency.catalog_synchronized','agency',0,{**counts,'removed_codes':codes,'removed_request_ids':request_ids,'removed_staff_ids':staff_ids})
    db.flush()
    return counts
