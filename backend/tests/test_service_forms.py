from sqlalchemy.orm import Session
from backend.app.models import Agency
from backend.tests.conftest import seed_actor, register, login
from backend.app.ml.schemas import Prediction

FIELDS = [
    {'key':'nama_usaha','label':'Nama usaha','type':'text','required':True,'max_length':30},
    {'key':'jumlah','label':'Jumlah pekerja','type':'number','required':True,'min_value':1,'max_value':100},
    {'key':'tanggal','label':'Tanggal mulai','type':'date','required':True},
    {'key':'jenis','label':'Jenis usaha','type':'select','required':True,'options':['Jasa','Dagang']},
    {'key':'setuju','label':'Persetujuan','type':'checkbox','required':True},
    {'key':'catatan','label':'Catatan tambahan','type':'textarea','max_length':100},
]
ANSWERS = {'nama_usaha':'Usaha Warga','jumlah':2,'tanggal':'2026-10-10','jenis':'Jasa','setuju':False}


def form_setup(appdb):
    c, engine, app = appdb
    with Session(engine) as db:
        agency = Agency(code='perizinan',name='Perizinan')
        db.add(agency);db.commit();agency_id=agency.id
    seed_actor(engine,'admin','admin@forms.id')
    login(c,'admin@forms.id')
    class Fixed:
        def predict(self, text):
            return Prediction('perizinan',{'perizinan':.9},.9,True,'form-test')
    app.state.classifier=Fixed()
    response=c.post('/api/v1/service-forms',json={'agency_id':agency_id,'title':'Formulir izin usaha','fields':FIELDS})
    assert response.status_code==201,response.text
    return c,engine,app,response.json()


def publish(c, form):
    response=c.post(f"/api/v1/service-forms/{form['id']}/publish",json={'expected_version':form['draft']['version']})
    assert response.status_code==200,response.text
    return response.json()


def test_forms_roles_and_immutable_publication(appdb):
    c,_,_,form=form_setup(appdb)
    register(c);login(c)
    assert c.get('/api/v1/service-forms').json()==[]
    assert c.get(f"/api/v1/service-forms/{form['id']}").status_code==404
    assert c.post('/api/v1/service-forms',json={'agency_id':form['agency_id'],'title':'Unauthorized','fields':FIELDS}).status_code==403
    login(c,'admin@forms.id');form=publish(c,form)
    assert form['published']['version']==1
    assert c.post(f"/api/v1/service-forms/{form['id']}/publish",json={'expected_version':1}).status_code==409
    edited=c.patch(f"/api/v1/service-forms/{form['id']}/draft",json={'expected_version':1,'fields':[{'key':'nama_usaha','label':'Nama baru','type':'text','required':True}]}).json()
    assert edited['draft']['version']==2 and edited['published']['schema']['fields'][0]['label']=='Nama usaha'
    assert c.patch(f"/api/v1/service-forms/{form['id']}/draft",json={'expected_version':1,'fields':FIELDS}).status_code==409
    publish(c,edited)
    login(c)
    public=c.get(f"/api/v1/service-forms/{form['id']}").json()
    assert public['published']['version']==2 and public['draft'] is None


def test_form_schema_rejects_unknown_duplicate_and_oversized_fields(appdb):
    c,_,_,form=form_setup(appdb)
    base={'agency_id':form['agency_id'],'title':'Schema test'}
    for fields in ([FIELDS[0],FIELDS[0]], [{'key':'bad','label':'Bad','type':'script'}], [{'key':f'f{i}','label':'Text','type':'text'} for i in range(31)], [{'key':'pick','label':'Pick','type':'select','options':[]}], [{'key':'num','label':'Number','type':'number','min_value':3,'max_value':1}], [{**FIELDS[0],'expression':'run()'}]):
        assert c.post('/api/v1/service-forms',json={**base,'fields':fields}).status_code==422
