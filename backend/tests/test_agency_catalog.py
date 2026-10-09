from sqlalchemy import select,func
from sqlalchemy.orm import Session
from backend.app.models import Agency,User,Request,RequestWorkflow,utcnow


def test_catalog_preserves_ids_removes_related_demo_and_seed_is_repeatable(appdb):
    from backend.app.agencies.catalog import AGENCIES,synchronize_catalog
    from backend.app.seed import seed
    _,engine,_=appdb
    with Session(engine) as db:
        kept=Agency(code='dukcapil',name='Dukcapil lama',sla_days=5)
        dummy=Agency(code='pajak',name='Badan Pendapatan Daerah')
        db.add_all([kept,dummy]);db.flush();kept_id=kept.id
        citizen=User(name='Demo',email='warga@demo.sgwa.id',password_hash='unused',role='citizen')
        staff=User(name='Petugas',email='pajak@demo.sgwa.id',password_hash='unused',role='staff',agency_id=dummy.id)
        db.add_all([citizen,staff]);db.flush()
        request=Request(reference='fixture',citizen_id=citizen.id,title='Demo',description='Demo terkait instansi lama',assigned_agency_id=dummy.id)
        db.add(request);db.flush();db.add(RequestWorkflow(request_id=request.id,agency_id=dummy.id,due_at=utcnow()));db.commit()
        counts=synchronize_catalog(db);db.commit()
        assert counts['removed_agencies']==1 and counts['removed_requests']==1 and counts['removed_staff']==1
        assert db.scalar(select(func.count()).select_from(Agency))==25
        assert db.get(Agency,kept_id).name=='DINAS KEPENDUDUKAN DAN PENCATATAN SIPIL'
        assert db.get(Agency,kept_id).sla_days==5
        assert db.scalar(select(User).where(User.email=='pajak@demo.sgwa.id')) is None
        assert db.scalar(select(func.count()).select_from(Request))==0
        seed(db,'PasswordDemo123!');seed(db,'PasswordDemo123!')
        assert set(db.scalars(select(Agency.name)))=={name for _,name in AGENCIES}
        assert db.scalar(select(func.count()).select_from(User).where(User.role=='staff'))==3


def test_catalog_refuses_to_delete_non_demo_dependencies(appdb):
    from backend.app.agencies.catalog import synchronize_catalog
    import pytest
    _,engine,_=appdb
    with Session(engine) as db:
        dummy=Agency(code='pajak',name='Badan Pendapatan Daerah');db.add(dummy);db.flush()
        db.add(User(name='Petugas nyata',email='petugas@example.com',password_hash='unused',role='staff',agency_id=dummy.id));db.commit()
        with pytest.raises(ValueError,match='non-demo'):synchronize_catalog(db)
        db.rollback()
        assert db.scalar(select(func.count()).select_from(Agency))==1
