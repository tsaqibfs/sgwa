from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError


async def database_error(request: Request,exc: SQLAlchemyError):
    return JSONResponse(status_code=503,content={'detail':'Database belum tersedia. Input Anda dapat dicoba kembali setelah layanan aktif.'})
