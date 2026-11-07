"""FastAPI application — a thin REST adapter over service.Service.

   POST   /api/transcribe        multipart upload -> 202 {job_id, status, poll_url}
   GET    /api/transcribe/{id}   job status / result
   DELETE /api/transcribe/{id}   cancel and delete
   GET    /api/health            engine, limits, queue

Run:  uvicorn lyravox_ai.api:app --host 0.0.0.0 --port $PORT
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .errors import ApiError
from .service import Service

service = None


def get_service():
    global service
    if service is None:
        service = Service()
    return service


@asynccontextmanager
async def lifespan(app):
    svc = get_service()
    if os.environ.get('PRELOAD_MODEL', '1') == '1' and svc.transcriber.name == 'faster-whisper' and svc.transcriber.installed():
        import threading
        threading.Thread(target=svc.transcriber.warm_up, daemon=True).start()     # load the model in the background; /api/health answers meanwhile
    yield
    svc.shutdown()


app = FastAPI(title='LYRAVOX AI', version='1.1.0', lifespan=lifespan)
_cfg = get_service().cfg


@app.middleware('http')
async def reject_oversize_early(request: Request, call_next):
    """Refuse an oversized upload from its Content-Length header before the framework spools the body to disk.
    (Added BEFORE the CORS middleware so that CORS is the outer layer and the browser can read this error.)"""
    if request.method == 'POST' and request.url.path == '/api/transcribe':
        cl = request.headers.get('content-length')
        if cl is None or not cl.isdigit():
            return JSONResponse(ApiError(411, 'length_required', 'Content-Length is required.').body(), status_code=411)
        if int(cl) > _cfg.max_upload_bytes + 1_000_000:
            return JSONResponse(ApiError(413, 'file_too_large', f'The file is larger than the {_cfg.max_upload_mb} MB limit.').body(), status_code=413)
    return await call_next(request)

_origins = _cfg.allowed_origins
app.add_middleware(CORSMiddleware, allow_origins=_origins, allow_credentials=False, allow_methods=['GET', 'POST', 'DELETE', 'OPTIONS'],
                   allow_headers=['*'], max_age=600)


@app.exception_handler(ApiError)
async def api_error(_req, exc):
    return JSONResponse(exc.body(), status_code=exc.status)


def client_of(request: Request):
    fwd = request.headers.get('x-forwarded-for')           # behind Render's proxy the real client is the first entry
    return (fwd.split(',')[0].strip() if fwd else (request.client.host if request.client else 'unknown'))


@app.get('/api/health')
def health():
    return get_service().health()


@app.post('/api/transcribe', status_code=202)
async def create(request: Request, file: UploadFile = File(...), language: str = Form('auto'), vocal_separation: str = Form(''),
                 word_timestamps: str = Form(''), clip_start: str = Form(''), clip_end: str = Form('')):
    svc = get_service()
    cl = request.headers.get('content-length')
    params = svc.parse_params({'language': language, 'vocal_separation': vocal_separation, 'word_timestamps': word_timestamps,
                               'clip_start': clip_start, 'clip_end': clip_end})

    def chunks():
        while True:
            b = file.file.read(1024 * 1024)
            if not b:
                break
            yield b
    from starlette.concurrency import run_in_threadpool
    job = await run_in_threadpool(svc.create_job, file.filename, chunks(), params, client_of(request), int(cl) if cl and cl.isdigit() else None)
    return {'job_id': job.id, 'status': job.status, 'poll_url': f'/api/transcribe/{job.id}'}


@app.get('/api/transcribe/{job_id}')
def status(job_id: str):
    return get_service().get(job_id)


@app.delete('/api/transcribe/{job_id}')
def remove(job_id: str):
    return get_service().delete(job_id)
