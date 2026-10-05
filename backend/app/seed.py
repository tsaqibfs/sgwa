from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.config import get_settings
from backend.app.db import get_engine
from backend.app.models import Agency,User
from backend.app.auth.service import hash_password
DEMO_DOMAIN='demo.sgwa.id'


def seed(db: Session,password: str):
    if len(password)<10:
        raise ValueError('DEMO_PASSWORD minimal 10 karakter.')
    for code,name in [('dukcapil','Dinas Kependudukan & Catatan Sipil'),('perizinan','Dinas Penanaman Modal & Perizinan'),('pajak','Badan Pendapatan Daerah'),('kesehatan','Dinas Kesehatan')]:
        agency=db.scalar(select(Agency).where(Agency.code==code))
        if not agency:
            agency=Agency(code=code,name=name);db.add(agency);db.flush()
        email=f'{code}@{DEMO_DOMAIN}'
        if not db.scalar(select(User).where(User.email==email)):
            db.add(User(name=f'Petugas {name}',email=email,password_hash=hash_password(password),role='staff',agency_id=agency.id))
    for role,email,name in [('citizen','warga@'+DEMO_DOMAIN,'Nadia Pratama'),('admin','admin@'+DEMO_DOMAIN,'Admin SGWA')]:
        if not db.scalar(select(User).where(User.email==email)):
            db.add(User(name=name,email=email,password_hash=hash_password(password),role=role))
    db.commit()


if __name__=='__main__':
    with Session(get_engine()) as db:
        seed(db,get_settings().demo_password)
    print('Akun demo siap. Password berasal dari DEMO_PASSWORD, akun lama tidak diubah.')
