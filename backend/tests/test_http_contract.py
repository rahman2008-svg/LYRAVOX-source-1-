"""REAL HTTP tests of the REST contract (real sockets, multipart uploads) against the stdlib dev server, which shares service.py with
the FastAPI app. The speech engine is the TEST-ONLY placeholder. The same contract tests run against the FastAPI app in
test_fastapi_app.py when fastapi + httpx are installed."""
import os, shutil, threading, time, unittest
import requests
from helpers import *
from lyravox_ai import devserver


class ContractMixin:
    """Subclasses provide self.base and self.svc."""
    def post(self, path=None, **kw):
        path = path or self.wav
        with open(path, 'rb') as f:
            return requests.post(self.base + '/api/transcribe', files={'file': (os.path.basename(path), f.read(), 'application/octet-stream')}, data=kw.get('data', {}), timeout=30)

    def poll(self, jid, timeout=60):
        t0 = time.time()
        while time.time() - t0 < timeout:
            r = requests.get(f'{self.base}/api/transcribe/{jid}', timeout=10)
            self.assertEqual(r.status_code, 200)
            if r.json()['status'] in ('completed', 'failed', 'cancelled'): return r.json()
            time.sleep(0.05)
        self.fail('timeout')

    def test_health(self):
        r = requests.get(self.base + '/api/health', timeout=10); j = r.json()
        self.assertEqual(r.status_code, 200); self.assertEqual(j['languages'], ['bn', 'en', 'hi']); self.assertIn('limits', j)

    def test_post_get_flow_matches_documented_schema(self):
        r = self.post(data={'language': 'bn', 'word_timestamps': 'true'})
        self.assertEqual(r.status_code, 202); j = r.json()
        self.assertEqual(set(j), {'job_id', 'status', 'poll_url'}); self.assertEqual(j['poll_url'], '/api/transcribe/' + j['job_id'])
        st = self.poll(j['job_id'])
        self.assertEqual(st['status'], 'completed'); self.assertEqual(st['language'], 'bn')
        s0 = st['segments'][0]
        self.assertEqual(set(s0) >= {'id', 'start', 'end', 'text', 'confidence', 'words', 'approx_timing'}, True)
        self.assertGreater(s0['end'], s0['start']); self.assertEqual(len(s0['words']), 3)   # 'TEST', 'LINE', 'n'
        self.assertEqual(r.headers.get('Access-Control-Allow-Origin'), '*')

    def test_cors_preflight(self):
        r = requests.options(self.base + '/api/transcribe', headers={'Origin': 'https://x.test', 'Access-Control-Request-Method': 'POST'}, timeout=10)
        self.assertIn(r.status_code, (200, 204)); self.assertEqual(r.headers.get('Access-Control-Allow-Origin'), '*')

    def test_errors_are_structured(self):
        r = self.post(os.path.join(self.d, 'bad.txt')); self.assertEqual(r.status_code, 415); self.assertEqual(r.json()['error']['code'], 'unsupported_type')
        r = self.post(os.path.join(self.d, 'liar.mp3')); self.assertEqual(r.status_code, 422); self.assertEqual(r.json()['error']['code'], 'invalid_audio')
        r = self.post(data={'language': 'zz'}); self.assertEqual(r.status_code, 422); self.assertEqual(r.json()['error']['code'], 'unsupported_language')
        r = requests.get(self.base + '/api/transcribe/' + '0' * 32, timeout=10); self.assertEqual(r.status_code, 404); self.assertEqual(r.json()['error']['code'], 'job_not_found')
        r = requests.delete(self.base + '/api/transcribe/' + '0' * 32, timeout=10); self.assertEqual(r.status_code, 404)
        r = requests.post(self.base + '/api/transcribe', data={'language': 'bn'}, timeout=10); self.assertEqual(r.status_code, 422)     # no file

    def test_oversize_rejected_413(self):
        r = self.post(self.big); self.assertEqual(r.status_code, 413); self.assertEqual(r.json()['error']['code'], 'file_too_large')

    def test_delete_cancels_and_removes(self):
        jid = self.post(self.long_, data={'language': 'en'}).json()['job_id']
        r = requests.delete(f'{self.base}/api/transcribe/{jid}', timeout=10)
        self.assertEqual(r.status_code, 200); self.assertEqual(r.json()['status'], 'cancelled')
        self.assertEqual(requests.get(f'{self.base}/api/transcribe/{jid}', timeout=10).status_code, 404)


class DevServerContract(ContractMixin, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = tmpdir()
        cls.wav = make_audio(os.path.join(cls.d, 'a.wav'), 10.0, 3.0, 2.0)
        cls.long_ = make_audio(os.path.join(cls.d, 'long.wav'), 24.0, 2.0, 2.0)
        cls.big = make_audio(os.path.join(cls.d, 'big.wav'), 70.0, 60.0, 1.0)
        with open(os.path.join(cls.d, 'bad.txt'), 'wb') as f: f.write(b'hi')
        with open(os.path.join(cls.d, 'liar.mp3'), 'wb') as f: f.write(os.urandom(30000))
        cls.svc, cfg, cls.eng = make_service(delay=0.3, max_upload_mb=1, max_active_per_ip=50, max_queue=50)
        cls.srv = devserver.serve(cls.svc, '127.0.0.1', 0)
        cls.base = f'http://127.0.0.1:{cls.srv.server_address[1]}'
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown(); cls.srv.server_close(); cls.svc.shutdown(); shutil.rmtree(cls.d, ignore_errors=True)


if __name__ == '__main__':
    unittest.main()
