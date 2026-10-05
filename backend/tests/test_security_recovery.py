import time
import jwt
from fastapi.testclient import TestClient
from backend.app.main import create_app
from backend.app.config import get_settings


def test_csrf_bootstrap_clears_expired_session():
    with TestClient(create_app()) as client:
        token=jwt.encode({'sub':'1','jti':'old','kind':'session','exp':time.time()-60},get_settings().jwt_secret,algorithm='HS256')
        client.cookies.set('sgwa_session',token,domain='testserver.local',path='/')
        response=client.get('/api/v1/auth/csrf')
        assert response.status_code==200
        assert client.cookies.get('sgwa_session') is None


def test_demo_emails_are_valid_login_inputs():
    from backend.app.seed import DEMO_DOMAIN
    from backend.app.auth.schemas import Credentials
    assert str(Credentials(email='admin@'+DEMO_DOMAIN,password='PasswordDemo123!').email)=='admin@demo.sgwa.id'


def test_protected_submission_without_session_requests_login():
    with TestClient(create_app()) as client:
        response=client.post('/api/v1/requests',headers={'Origin':get_settings().trusted_origins[0]},json={'title':'Pengurusan KTP','description':'Saya ingin mengurus kartu identitas penduduk.'})
        assert response.status_code==401
