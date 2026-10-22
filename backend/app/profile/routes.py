from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
from backend.app.db import get_session
from backend.app.models import User
from backend.app.auth.dependencies import get_current_user
from backend.app.profile.schemas import ProfileOut, ProfileUpdate, PasswordChange
from backend.app.profile.service import update_profile, change_password

router = APIRouter(prefix='/profile', tags=['Profil'])


@router.get('', response_model=ProfileOut)
def profile(actor: User = Depends(get_current_user)):
    return actor


@router.patch('', response_model=ProfileOut)
def update(payload: ProfileUpdate, actor: User = Depends(get_current_user), db: Session = Depends(get_session)):
    return update_profile(db, actor, payload)


@router.post('/password')
def password(payload: PasswordChange, response: Response, actor: User = Depends(get_current_user), db: Session = Depends(get_session)):
    change_password(db, actor, payload)
    response.delete_cookie('sgwa_session')
    response.delete_cookie('sgwa_csrf')
    return {'message': 'Password diperbarui. Silakan masuk kembali.'}
