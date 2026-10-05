import secrets
from datetime import datetime, timedelta, timezone
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, InvalidHashError
from backend.app.config import get_settings

hasher=PasswordHasher()
DUMMY_HASH=hasher.hash('not-an-account-password')


def hash_password(password: str) -> str:
    return hasher.hash(password)


def verify_password(password: str, encoded: str) -> bool:
    try:
        return hasher.verify(encoded,password)
    except (VerificationError,InvalidHashError):
        return False


def make_session(user_id: int) -> tuple[str,str]:
    sid=secrets.token_urlsafe(24)
    token=jwt.encode({'sub':str(user_id),'jti':sid,'kind':'session','exp':datetime.now(timezone.utc)+timedelta(minutes=30)},get_settings().jwt_secret,algorithm='HS256')
    return token,make_csrf(sid)


def make_csrf(sid: str='anonymous') -> str:
    return jwt.encode({'nonce':secrets.token_urlsafe(24),'sid':sid,'kind':'csrf','exp':datetime.now(timezone.utc)+timedelta(minutes=30)},get_settings().jwt_secret,algorithm='HS256')


def decode(token: str, kind: str) -> dict:
    payload=jwt.decode(token,get_settings().jwt_secret,algorithms=['HS256'],options={'require':['exp','kind']})
    if payload['kind']!=kind:
        raise jwt.InvalidTokenError('Wrong token kind')
    return payload
