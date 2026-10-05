from backend.tests.conftest import register, login


def test_registration_login_logout(appdb):
    client,_,_=appdb
    assert register(client).status_code==201
    assert register(client,'WARGA@example.com').status_code==409
    assert login(client,password='IncorrectPassword').status_code==401
    response=login(client)
    assert response.status_code==200
    assert response.json()['user']['role']=='citizen'
    assert 'password_hash' not in response.text
    assert 'HttpOnly' in response.headers['set-cookie']
    assert 'Max-Age=1800' in response.headers['set-cookie']
    assert client.get('/api/v1/auth/me').status_code==200
    assert client.post('/api/v1/auth/logout').status_code==200
    assert client.get('/api/v1/auth/me').status_code==401


def test_role_injection_and_security_checks(appdb):
    client,_,_=appdb
    payload={'name':'Warga','email':'bad@example.com','password':'PasswordDemo123!','role':'admin'}
    assert client.post('/api/v1/auth/register',json=payload).status_code==422
    client.headers['X-CSRF-Token']='wrong'
    assert register(client).status_code==403
    client.headers['X-CSRF-Token']=client.get('/api/v1/auth/csrf').json()['csrf_token']
    client.headers['Origin']='https://evil.example'
    assert register(client).status_code==403


def test_expired_token_is_rejected(appdb):
    import jwt
    from backend.app.config import get_settings
    client,_,_=appdb
    register(client);login(client)
    client.cookies.clear()
    client.cookies.set('sgwa_session',jwt.encode({'sub':'1','exp':1,'csrf':'x'},get_settings().jwt_secret,algorithm='HS256'))
    assert client.get('/api/v1/auth/me').status_code==401
