"""Dependency-free development server with the SAME REST contract as api.py (standard library only).

For local development and for the automated tests, where FastAPI / uvicorn may not be installed. It reads the whole upload into
memory (fine for development, which is why production uses api.py). Run:

    python -m lyravox_ai.devserver --port 8000                # real engine (needs faster-whisper)
    LYRAVOX_ALLOW_FAKE=1 python -m lyravox_ai.devserver --fake   # placeholder engine for plumbing tests only
"""
import argparse, json, re, sys, threading
from email.parser import BytesParser
from email.policy import default as email_policy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from .errors import ApiError
from .service import Service


def parse_multipart(content_type, body):
    msg = BytesParser(policy=email_policy).parsebytes(b'Content-Type: ' + content_type.encode() + b'\r\nMIME-Version: 1.0\r\n\r\n' + body)
    fields, files = {}, {}
    if not msg.is_multipart():
        raise ApiError(422, 'invalid_request', 'Expected a multipart/form-data upload.')
    for part in msg.iter_parts():
        name = part.get_param('name', header='content-disposition')
        fn = part.get_filename()
        data = part.get_payload(decode=True) or b''
        if fn is not None:
            files[name] = (fn, data)
        elif name:
            fields[name] = data.decode('utf-8', 'replace')
    return fields, files


def make_handler(service):
    cfg = service.cfg

    class H(BaseHTTPRequestHandler):
        protocol_version = 'HTTP/1.1'

        def log_message(self, fmt, *a):
            pass

        def _send(self, status, obj):
            body = json.dumps(obj, ensure_ascii=False).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self._cors()
            self.end_headers()
            self.wfile.write(body)

        def _cors(self):
            o = self.headers.get('Origin')
            allow = cfg.allowed_origins
            if '*' in allow:
                self.send_header('Access-Control-Allow-Origin', '*')
            elif o and o in allow:
                self.send_header('Access-Control-Allow-Origin', o); self.send_header('Vary', 'Origin')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', '*')

        def do_OPTIONS(self):
            self.send_response(204); self._cors(); self.send_header('Content-Length', '0'); self.end_headers()

        def _guard(self, fn):
            try:
                fn()
            except ApiError as e:
                self._send(e.status, e.body())
            except Exception as e:
                self._send(500, {'error': {'code': 'internal_error', 'message': f'{type(e).__name__}: {e}'}})

        def do_GET(self):
            def go():
                path = self.path.split('?')[0]
                if path == '/api/health':
                    return self._send(200, service.health())
                m = re.fullmatch(r'/api/transcribe/([0-9a-f]+)', path)
                if m:
                    return self._send(200, service.get(m.group(1)))
                raise ApiError(404, 'not_found', 'No such endpoint.')
            self._guard(go)

        def do_DELETE(self):
            def go():
                m = re.fullmatch(r'/api/transcribe/([0-9a-f]+)', self.path.split('?')[0])
                if not m:
                    raise ApiError(404, 'not_found', 'No such endpoint.')
                self._send(200, service.delete(m.group(1)))
            self._guard(go)

        def do_POST(self):
            def go():
                if self.path.split('?')[0] != '/api/transcribe':
                    raise ApiError(404, 'not_found', 'No such endpoint.')
                cl = self.headers.get('Content-Length')
                if cl is None or not cl.isdigit():
                    raise ApiError(411, 'length_required', 'Content-Length is required.')
                n = int(cl)
                if n > cfg.max_upload_bytes + 1_000_000:
                    # drain a bounded amount so the client gets the answer instead of a reset, then refuse
                    self.rfile.read(min(n, 2_000_000))
                    self.close_connection = True
                    raise ApiError(413, 'file_too_large', f'The file is larger than the {cfg.max_upload_mb} MB limit.')
                body = self.rfile.read(n)
                fields, files = parse_multipart(self.headers.get('Content-Type', ''), body)
                if 'file' not in files:
                    raise ApiError(422, 'missing_file', "Field 'file' (the audio upload) is required.")
                params = service.parse_params(fields)
                fn, data = files['file']
                job = service.create_job(fn, iter([data]), params, self.client_address[0], n)
                self._send(202, {'job_id': job.id, 'status': job.status, 'poll_url': f'/api/transcribe/{job.id}'})
            self._guard(go)
    return H


def serve(service, host='127.0.0.1', port=8000):
    srv = ThreadingHTTPServer((host, port), make_handler(service))
    srv.daemon_threads = True
    return srv


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--host', default='127.0.0.1'); ap.add_argument('--port', type=int, default=8000)
    ap.add_argument('--fake', action='store_true', help='TEST ONLY placeholder engine (needs LYRAVOX_ALLOW_FAKE=1)')
    ap.add_argument('--fake-delay', type=float, default=0.0, help='TEST ONLY: seconds per placeholder line')
    ap.add_argument('--fake-fail', action='store_true', help='TEST ONLY: make the placeholder engine raise')
    a = ap.parse_args()
    from .config import Config
    cfg = Config.from_env()
    tr = None
    if a.fake:
        from .engines import FakeTestTranscriber
        tr = FakeTestTranscriber(cfg, delay=a.fake_delay, fail_on='transcribe' if a.fake_fail else None)
    svc = Service(cfg, tr)
    print(f'LYRAVOX AI dev server on http://{a.host}:{a.port}  engine={svc.transcriber.name}', file=sys.stderr)
    serve(svc, a.host, a.port).serve_forever()
