"""The same contract tests against the real FastAPI app. SKIPPED automatically when fastapi / httpx / python-multipart are not installed
(they are not in the sandbox this repository was developed in) — install backend/requirements-dev.txt to run them."""
import importlib.util, os, shutil, unittest
from helpers import *
from test_http_contract import ContractMixin

HAVE = all(importlib.util.find_spec(m) for m in ('fastapi', 'httpx', 'multipart'))


@unittest.skipUnless(HAVE, 'fastapi / httpx / python-multipart are not installed: FastAPI app NOT tested in this environment')
class FastApiContract(ContractMixin, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import threading, uvicorn
        os.environ['PRELOAD_MODEL'] = '0'
        from lyravox_ai import api
        svc, cfg, eng = make_service(delay=0.3, max_upload_mb=1, max_active_per_ip=50, max_queue=50)
        api.service = svc
        cls.svc = svc
        cls.server = uvicorn.Server(uvicorn.Config(api.app, host='127.0.0.1', port=0, log_level='warning'))
        threading.Thread(target=cls.server.run, daemon=True).start()
        import time
        while not cls.server.started: time.sleep(0.05)
        cls.base = f'http://127.0.0.1:{cls.server.servers[0].sockets[0].getsockname()[1]}'
        cls.d = tmpdir()
        cls.wav = make_audio(os.path.join(cls.d, 'a.wav'), 10.0, 3.0, 2.0)
        cls.long_ = make_audio(os.path.join(cls.d, 'long.wav'), 24.0, 2.0, 2.0)
        cls.big = make_audio(os.path.join(cls.d, 'big.wav'), 70.0, 60.0, 1.0)
        with open(os.path.join(cls.d, 'bad.txt'), 'wb') as f: f.write(b'hi')
        with open(os.path.join(cls.d, 'liar.mp3'), 'wb') as f: f.write(os.urandom(30000))

    @classmethod
    def tearDownClass(cls):
        cls.server.should_exit = True; cls.svc.shutdown(); shutil.rmtree(cls.d, ignore_errors=True)


if __name__ == '__main__':
    unittest.main()
