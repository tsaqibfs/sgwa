import io
from sqlalchemy.orm import Session
from backend.app.models import Agency
from backend.tests.conftest import seed_actor, register, login


def test_attachment_upload_and_download(appdb,monkeypatch,tmp_path):
    c, engine, app = appdb
    from backend.app.ml.schemas import Prediction
    from backend.app.config import get_settings
    monkeypatch.setattr(get_settings(),'upload_dir',tmp_path)
    class Fixed:
        def predict(self,text):return Prediction('dukcapil',{'dukcapil':.99},.99,True,'attachment-fixture')
    app.state.classifier=Fixed()
    with Session(engine) as db:
        agency = Agency(code='dukcapil', name='Dinas Dukcapil')
        db.add(agency)
        db.commit()
        agency_id = agency.id

    seed_actor(engine, 'citizen', 'warga@upload.id')
    seed_actor(engine, 'staff', 'staf@upload.id', agency_id=agency_id)
    seed_actor(engine, 'admin', 'admin@upload.id')

    # Login citizen
    login(c, 'warga@upload.id')

    # Test invalid extension
    bad_file = io.BytesIO(b'malicious content')
    res_bad = c.post('/api/v1/attachments/upload', files={'file': ('script.exe', bad_file, 'application/octet-stream')})
    assert res_bad.status_code == 422
    assert 'Format file tidak didukung' in res_bad.json()['detail']

    # Test valid PDF upload
    pdf_content = b'%PDF-1.4 mock pdf content'
    pdf_file = io.BytesIO(pdf_content)
    res_pdf = c.post(
        '/api/v1/attachments/upload',
        files={'file': ('ktp_warga.pdf', pdf_file, 'application/pdf')},
        data={'description': 'Salinan KTP Asli'}
    )
    assert res_pdf.status_code == 200, res_pdf.text
    att_data = res_pdf.json()
    assert att_data['filename'] == 'ktp_warga.pdf'
    assert att_data['description'] == 'Salinan KTP Asli'
    att_id = att_data['id']

    # Download by owner
    res_dl = c.get(f'/api/v1/attachments/{att_id}/download')
    assert res_dl.status_code == 200
    assert res_dl.content == pdf_content

    # Now create a request linked to this attachment
    res_req = c.post('/api/v1/requests', json={
        'title': 'Pengurusan KTP Baru',
        'description': 'Saya ingin mengurus KTP dan kartu keluarga penduduk di Dukcapil.',
        'attachment_ids': [att_id]
    })
    assert res_req.status_code == 201, res_req.text
    req_id = res_req.json()['id']

    # Citizen uploads supporting document directly to the request for Dukcapil
    doc_content = b'Docx test content'
    doc_file = io.BytesIO(doc_content)
    res_req_att = c.post(
        f'/api/v1/requests/{req_id}/attachments',
        files={'file': ('persyaratan_dukcapil.docx', doc_file, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')},
        data={'agency_id': str(agency_id), 'description': 'Surat Keterangan RT/RW'}
    )
    assert res_req_att.status_code == 200, res_req_att.text
    req_att_id = res_req_att.json()['id']
    assert res_req_att.json()['agency_name'] == 'Dinas Dukcapil'

    # Check request attachments listing
    res_list = c.get(f'/api/v1/requests/{req_id}/attachments')
    assert res_list.status_code == 200
    assert len(res_list.json()) >= 1

    # Staff of Dukcapil can view and download
    login(c, 'staf@upload.id')
    res_staff_list = c.get(f'/api/v1/requests/{req_id}/attachments')
    assert res_staff_list.status_code == 200
    res_staff_dl = c.get(f'/api/v1/attachments/{req_att_id}/download')
    assert res_staff_dl.status_code == 200
    assert res_staff_dl.content == doc_content

    # Other citizen cannot download
    seed_actor(engine, 'citizen', 'lain@upload.id')
    login(c, 'lain@upload.id')
    res_forbidden = c.get(f'/api/v1/attachments/{req_att_id}/download')
    assert res_forbidden.status_code == 403

    # Admin can download and delete
    login(c, 'admin@upload.id')
    res_admin_dl = c.get(f'/api/v1/attachments/{req_att_id}/download')
    assert res_admin_dl.status_code == 200

    res_del = c.delete(f'/api/v1/attachments/{req_att_id}')
    assert res_del.status_code == 200
    assert res_del.json()['status'] == 'deleted'

    # Confirm it is gone
    assert c.get(f'/api/v1/attachments/{req_att_id}/download').status_code == 404
    from sqlalchemy import select
    from backend.app.models import Request,RequestEvent
    with Session(engine) as db:
        request=db.get(Request,req_id)
        events=db.scalars(select(RequestEvent).where(RequestEvent.request_id==req_id,RequestEvent.event_type.in_(['attachment_added','attachment_removed']))).all()
        assert {event.event_type for event in events}=={'attachment_added','attachment_removed'}
        assert all(event.from_status==event.to_status==request.status for event in events)
