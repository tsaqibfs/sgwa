import secrets
from contextlib import asynccontextmanager
import jwt
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from backend.app.config import get_settings
from backend.app.auth.routes import router as auth_router
from backend.app.auth.service import decode
from backend.app.ml.classifier import Classifier, ModelUnavailable
from backend.app.errors import database_error
from backend.app.requests.routes import router as request_router
from backend.app.agencies.routes import router as agency_router
from backend.app.dashboard.routes import router as dashboard_router
from backend.app.ml.routes import router as ml_router
from backend.app.workflow.routes import router as workflow_router
from backend.app.live.routes import router as live_router
from backend.app.audit.routes import router as audit_router
from backend.app.profile.routes import router as profile_router


@asynccontextmanager
async def lifespan(app):
    try:
        app.state.classifier=Classifier(get_settings().model_dir)
    except ModelUnavailable:
        app.state.classifier=None
    yield


def create_app() -> FastAPI:
    application=FastAPI(title='SGWA API',version='0.1.0',lifespan=lifespan)
    application.add_exception_handler(SQLAlchemyError,database_error)

    @application.middleware('http')
    async def csrf_guard(request: Request,call_next):
        if request.method not in ('GET','HEAD','OPTIONS'):
            if request.headers.get('origin') not in get_settings().trusted_origins:
                return JSONResponse(status_code=403,content={'detail':'Origin tidak diizinkan.'})
            public_auth={'/api/v1/auth/login','/api/v1/auth/register','/api/v1/auth/logout'}
            if request.url.path not in public_auth and not request.cookies.get('sgwa_session'):
                return JSONResponse(status_code=401,content={'detail':'Sesi berakhir. Silakan masuk kembali.'})
            header=request.headers.get('x-csrf-token','')
            cookie=request.cookies.get('sgwa_csrf','')
            try:
                if not header or not secrets.compare_digest(header,cookie):
                    raise jwt.InvalidTokenError('Missing CSRF')
                csrf_data=decode(header,'csrf')
                sid='anonymous'
                if request.cookies.get('sgwa_session'):
                    try:
                        sid=decode(request.cookies['sgwa_session'],'session')['jti']
                    except (jwt.InvalidTokenError,KeyError):
                        return JSONResponse(status_code=401,content={'detail':'Sesi berakhir. Silakan masuk kembali.'})
                if csrf_data['sid']!=sid:
                    raise jwt.InvalidTokenError('Wrong CSRF session')
            except (jwt.InvalidTokenError,KeyError):
                return JSONResponse(status_code=403,content={'detail':'Validasi keamanan gagal. Muat ulang halaman.'})
        return await call_next(request)

    application.include_router(auth_router,prefix='/api/v1')
    application.include_router(request_router,prefix='/api/v1')
    application.include_router(agency_router,prefix='/api/v1')
    application.include_router(dashboard_router,prefix='/api/v1')
    application.include_router(ml_router,prefix='/api/v1')
    application.include_router(workflow_router,prefix='/api/v1')
    application.include_router(live_router,prefix='/api/v1')
    application.include_router(audit_router,prefix='/api/v1')
    application.include_router(profile_router,prefix='/api/v1')

    @application.get('/api/v1/health',tags=['Sistem'])
    def health():
        return {'status':'ok'}

    return application


app=create_app()
