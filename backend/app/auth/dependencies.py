from fastapi import Depends, HTTPException, Request
import jwt
from sqlalchemy.orm import Session
from backend.app.db import get_session
from backend.app.models import User
from backend.app.auth.service import decode


def get_current_user(request: Request, session: Session=Depends(get_session)) -> User:
    try:
        data=decode(request.cookies.get('sgwa_session',''),'session')
        user_id=int(data['sub'])
    except (jwt.InvalidTokenError,ValueError,KeyError):
        raise HTTPException(401,'Sesi berakhir. Silakan masuk kembali.')
    user=session.get(User,user_id)
    if user is None or not user.active:
        raise HTTPException(401,'Sesi tidak valid.')
    return user


def require_role(*roles: str):
    def check(actor: User=Depends(get_current_user)):
        if actor.role not in roles:
            raise HTTPException(403,'Anda tidak memiliki akses untuk tindakan ini.')
        return actor
    return check
