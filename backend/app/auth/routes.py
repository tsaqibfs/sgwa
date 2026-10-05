import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from backend.app.db import get_session
from backend.app.models import User
from backend.app.config import get_settings
from backend.app.auth.schemas import Credentials, Register, UserOut
from backend.app.auth.service import DUMMY_HASH, verify_password, hash_password, make_session, make_csrf, decode
from backend.app.auth.dependencies import get_current_user

router=APIRouter(prefix='/auth',tags=['Autentikasi'])


def set_csrf(response: Response,token: str):
    response.set_cookie('sgwa_csrf',token,max_age=1800,secure=get_settings().cookie_secure,samesite='lax',httponly=False)


@router.get('/csrf')
def csrf(request: Request,response: Response):
    sid='anonymous'
    try:
        sid=decode(request.cookies.get('sgwa_session',''),'session')['jti']
    except (jwt.InvalidTokenError,KeyError):
        response.delete_cookie('sgwa_session')
    token=make_csrf(sid);set_csrf(response,token)
    return {'csrf_token':token}


@router.post('/register',response_model=UserOut,status_code=201)
def register(payload: Register,db: Session=Depends(get_session)):
    user=User(name=payload.name,email=str(payload.email),password_hash=hash_password(payload.password),role='citizen')
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback();raise HTTPException(409,'Email sudah terdaftar.')
    return user


@router.post('/login')
def login(payload: Credentials,response: Response,db: Session=Depends(get_session)):
    user=db.scalar(select(User).where(User.email==str(payload.email)))
    valid=verify_password(payload.password,user.password_hash if user else DUMMY_HASH)
    if not user or not valid or not user.active:
        raise HTTPException(401,'Email atau password tidak sesuai.')
    token,csrf_token=make_session(user.id)
    response.set_cookie('sgwa_session',token,max_age=1800,secure=get_settings().cookie_secure,httponly=True,samesite='lax')
    set_csrf(response,csrf_token)
    return {'user':UserOut.model_validate(user).model_dump(),'csrf_token':csrf_token}


@router.post('/logout')
def logout(response: Response):
    response.delete_cookie('sgwa_session');response.delete_cookie('sgwa_csrf')
    return {'message':'Berhasil keluar.'}


@router.get('/me',response_model=UserOut)
def me(actor: User=Depends(get_current_user)):
    return actor
