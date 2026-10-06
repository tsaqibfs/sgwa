import asyncio
from fastapi import APIRouter,Request
from fastapi.responses import StreamingResponse
from backend.app.db import get_engine
from backend.app.live.service import session_snapshot,iter_events

router=APIRouter(tags=['Live updates'])


@router.get('/live')
async def live(request:Request):
    token=request.cookies.get('sgwa_session','');engine=get_engine()
    # Authenticate with a short-lived session before response headers are sent.
    await asyncio.to_thread(session_snapshot,engine,token)
    async def frames():
        async for frame in iter_events(engine,token):
            if await request.is_disconnected():return
            yield frame
    return StreamingResponse(frames(),media_type='text/event-stream',headers={'Cache-Control':'no-store','X-Accel-Buffering':'no'})
