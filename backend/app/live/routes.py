import asyncio
from collections import Counter
from fastapi import APIRouter,Request
from fastapi.responses import JSONResponse,StreamingResponse
from starlette.types import Receive, Scope, Send
from backend.app.db import get_engine
from backend.app.live.service import session_snapshot,iter_events

router=APIRouter(tags=['Live updates'])
MAX_STREAMS_PER_ACCOUNT = 4
active_streams: Counter[int] = Counter()


class AccountStream(StreamingResponse):
    def __init__(self, account_id: int, frames):
        super().__init__(frames, media_type='text/event-stream', headers={
            'Cache-Control': 'no-store', 'X-Accel-Buffering': 'no',
        })
        self.account_id = account_id

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        account_id = self.account_id
        if active_streams[account_id] >= MAX_STREAMS_PER_ACCOUNT:
            response = JSONResponse(
                {'detail': 'Terlalu banyak tab yang menerima pembaruan langsung.'},
                status_code=429, headers={'Retry-After': '5', 'Cache-Control': 'no-store'},
            )
            await response(scope, receive, send)
            return
        active_streams[account_id] += 1
        try:
            await super().__call__(scope, receive, send)
        finally:
            active_streams[account_id] -= 1
            if not active_streams[account_id]:
                del active_streams[account_id]


@router.get('/live')
async def live(request:Request):
    token=request.cookies.get('sgwa_session','');engine=get_engine()
    # Authenticate with a short-lived session before response headers are sent.
    scope, _ = await asyncio.to_thread(session_snapshot,engine,token)
    async def frames():
        async for frame in iter_events(engine,token):
            if await request.is_disconnected():return
            yield frame
    return AccountStream(scope[0], frames())
