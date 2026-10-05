from fastapi.testclient import TestClient
from backend.app.main import create_app


def test_admin_api_contract():
    schema=create_app().openapi()
    required=['/api/v1/agencies','/api/v1/staff','/api/v1/dashboard','/api/v1/ml/metadata','/api/v1/ml/evaluation']
    assert all(path in schema['paths'] for path in required)


def test_health_and_csrf_do_not_need_database():
    with TestClient(create_app()) as client:
        assert client.get('/api/v1/health').json()=={'status':'ok'}
        token=client.get('/api/v1/auth/csrf').json()['csrf_token']
        assert token
        assert client.post('/api/v1/auth/register',json={}).status_code==403
