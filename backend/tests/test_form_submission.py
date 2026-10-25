from backend.tests.test_service_forms import form_setup,publish,ANSWERS,FIELDS
from backend.tests.conftest import register,login
from backend.app.ml.schemas import Prediction


def body(form,answers=ANSWERS):
    return {'title':'Permohonan izin usaha','description':'Saya ingin mengurus izin usaha melalui dinas perizinan.','form_version_id':form['published']['id'],'form_answers':answers}


def test_form_answers_strict_and_historical_version_retained(appdb):
    c,_,_,draft=form_setup(appdb);form=publish(c,draft)
    register(c);login(c)
    response=c.post('/api/v1/requests',json=body(form));assert response.status_code==201,response.text
    item=response.json();assert item['form']['version']==1 and item['form']['answers']==ANSWERS
    invalid=[{**ANSWERS,'extra':'unknown'}, {**ANSWERS,'jumlah':'2'}, {**ANSWERS,'jumlah':0}, {**ANSWERS,'setuju':'false'}, {**ANSWERS,'tanggal':'2026-02-30'}, {**ANSWERS,'jenis':'Other'}, {**ANSWERS,'nama_usaha':'x'*31}, {k:v for k,v in ANSWERS.items() if k!='nama_usaha'}]
    for answers in invalid:
        assert c.post('/api/v1/requests',json=body(form,answers)).status_code==422
    assert c.post('/api/v1/requests',json={**body(form),'form_answers':None}).status_code==422
    login(c,'admin@forms.id')
    edited=c.patch(f"/api/v1/service-forms/{form['id']}/draft",json={'expected_version':1,'fields':[{**FIELDS[0],'label':'New label'}]}).json()
    publish(c,edited);login(c)
    assert c.post('/api/v1/requests',json=body(form)).status_code==409
    old=c.get(f"/api/v1/requests/{item['id']}").json()
    assert old['form']['schema']['fields'][0]['label']=='Nama usaha'


def test_form_mismatch_reviews_and_inactive_form_rejected(appdb):
    c,_,app,draft=form_setup(appdb);form=publish(c,draft)
    register(c);login(c)
    class Fixed:
        def predict(self,text):return Prediction('kesehatan',{'kesehatan':.95},.95,True,'mismatch-test')
    app.state.classifier=Fixed()
    item=c.post('/api/v1/requests',json=body(form)).json()
    assert item['status']=='escalated' and item['classification'] is None
    assert any('formulir' in e['note'].lower() for e in item['events'])
    login(c,'admin@forms.id')
    assert c.get(f"/api/v1/requests/{item['id']}").json()['classification']['needs_review']
    assert c.patch(f"/api/v1/service-forms/{form['id']}",json={'active':False}).status_code==200
    login(c);assert c.post('/api/v1/requests',json=body(form)).status_code==409


def test_huge_numeric_answer_rejected_without_server_error(appdb):
    c,_,_,draft=form_setup(appdb);form=publish(c,draft)
    register(c);login(c)
    assert c.post('/api/v1/requests',json=body(form,{**ANSWERS,'jumlah':10**400})).status_code==422
