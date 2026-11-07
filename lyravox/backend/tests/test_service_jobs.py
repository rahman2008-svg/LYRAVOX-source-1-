"""Service + job manager + pipeline. REAL: upload validation, ffmpeg decode / silence / chunking, job lifecycle, cancellation, timeouts,
concurrency limits, temp-file cleanup. MOCKED: the speech engine (FakeTestTranscriber / stubs) — no model is involved here."""
import os, resource, shutil, threading, time, unittest
from helpers import *
from lyravox_ai.errors import ApiError, AudioError
from lyravox_ai.engines import FakeTestTranscriber, RawSegment


def _w(path, data):
    with open(path, 'wb') as f: f.write(data)


def _r(path):
    with open(path, 'rb') as f: return f.read()


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = tmpdir()
        cls.wav10 = make_audio(os.path.join(cls.d, 'ten.wav'), 10.0, 3.0, 2.0)
        cls.svcs = []

    @classmethod
    def tearDownClass(cls):
        for s in cls.svcs: s.shutdown()
        shutil.rmtree(cls.d, ignore_errors=True)

    def svc(self, **kw):
        s, cfg, eng = make_service(**kw)
        self.svcs.append(s)
        return s, cfg, eng


class ValidationTests(Base):
    def test_rejects_unsupported_extension(self):
        s, cfg, _ = self.svc()
        p = os.path.join(self.d, 'x.txt'); _w(p, b'hello')
        with self.assertRaises(ApiError) as e: submit(s, p)
        self.assertEqual((e.exception.status, e.exception.code), (415, 'unsupported_type')); self.assertEqual(leftover(cfg), [])

    def test_rejects_fake_audio_content(self):
        s, cfg, _ = self.svc()
        p = os.path.join(self.d, 'liar.mp3'); _w(p, os.urandom(20000))
        with self.assertRaises(ApiError) as e: submit(s, p)
        self.assertEqual((e.exception.status, e.exception.code), (422, 'invalid_audio')); self.assertEqual(leftover(cfg), [])

    def test_rejects_empty_file(self):
        s, cfg, _ = self.svc()
        p = os.path.join(self.d, 'empty.wav'); open(p, 'wb').close()
        with self.assertRaises(ApiError) as e: submit(s, p)
        self.assertEqual(e.exception.code, 'empty_file'); self.assertEqual(leftover(cfg), [])

    def test_rejects_oversize_upload_while_streaming(self):
        s, cfg, _ = self.svc(max_upload_mb=1)
        big = make_audio(os.path.join(self.d, 'big.wav'), 70.0, 60.0, 1.0)          # ~2.2 MB of PCM
        self.assertGreater(os.path.getsize(big), 1024 * 1024)
        with self.assertRaises(ApiError) as e: s.create_job('big.wav', iter([_r(big)]), s.parse_params({}), 'c')    # no content-length given
        self.assertEqual((e.exception.status, e.exception.code), (413, 'file_too_large')); self.assertEqual(leftover(cfg), [])

    def test_rejects_oversize_by_content_length_before_reading(self):
        s, cfg, _ = self.svc(max_upload_mb=1)
        def boom():
            raise AssertionError('upload body must not be read')
            yield b''
        with self.assertRaises(ApiError) as e: s.create_job('a.wav', boom(), s.parse_params({}), 'c', content_length=50 * 1024 * 1024)
        self.assertEqual(e.exception.status, 413)

    def test_rejects_too_long_but_accepts_clip_of_it(self):
        s, cfg, _ = self.svc(max_duration_s=5)
        with self.assertRaises(ApiError) as e: submit(s, self.wav10)
        self.assertEqual((e.exception.status, e.exception.code), (413, 'duration_exceeded'))
        job = submit(s, self.wav10, {'clip_start': '1', 'clip_end': '5'})
        self.assertEqual(wait_done(s, job.id)['status'], 'completed')

    def test_parameter_validation(self):
        s, _, _ = self.svc()
        for bad in ({'language': 'xx'}, {'vocal_separation': 'maybe'}, {'clip_start': 'abc'}, {'clip_start': '-1'}, {'clip_start': '5', 'clip_end': '5.1'}):
            with self.subTest(bad=bad):
                with self.assertRaises(ApiError) as e: s.parse_params(bad)
                self.assertEqual(e.exception.status, 422)
        self.assertEqual(s.parse_params({'language': 'BN'})['language'], 'bn')
        self.assertEqual(s.parse_params({})['language'], 'auto')
        with self.assertRaises(ApiError): submit(s, self.wav10, {'clip_start': '999'})

    def test_filename_is_sanitised_in_status(self):
        s, _, _ = self.svc()
        p = os.path.join(self.d, 'my song (final) ../x.wav'.replace('../', ''))
        shutil.copy(self.wav10, p)
        st = wait_done(s, submit(s, p).id)
        self.assertRegex(st['input']['filename'], r'^[A-Za-z0-9._-]+$')


class LifecycleTests(Base):
    def test_completed_job_shape_progress_and_cleanup(self):
        s, cfg, eng = self.svc()
        job = submit(s, self.wav10, {'language': 'bn'})
        seen = []
        while True:
            st = s.get(job.id); seen.append(st['progress'])
            if st['status'] in ('completed', 'failed'): break
            time.sleep(0.01)
        self.assertEqual(st['status'], 'completed', st)
        self.assertEqual(seen, sorted(seen), 'progress went backwards'); self.assertEqual(st['progress'], 1.0)
        self.assertEqual(st['language'], 'bn'); self.assertEqual(st['engine'], 'fake-test-engine')
        segs = st['segments']
        self.assertEqual(len(segs), 2)
        self.assertAlmostEqual(segs[0]['start'], 0.0, delta=0.2); self.assertAlmostEqual(segs[0]['end'], 3.0, delta=0.2)    # tone 0-3 s
        self.assertAlmostEqual(segs[1]['start'], 5.0, delta=0.2); self.assertAlmostEqual(segs[1]['end'], 8.0, delta=0.2)    # tone 5-8 s
        self.assertTrue(all(k in segs[0] for k in ('id', 'start', 'end', 'text', 'confidence', 'words')))
        self.assertEqual(st['vocal_separation'], {'requested': False, 'used': False, 'error': None})
        self.assertEqual(leftover(cfg), [])

    def test_auto_language_detection_is_reported(self):
        s, _, _ = self.svc()
        st = wait_done(s, submit(s, self.wav10, {'language': 'auto'}).id)
        self.assertTrue(st['language_detected']); self.assertIn(st['language'], ('bn', 'en', 'hi')); self.assertIsNotNone(st['language_probability'])

    def test_clip_timestamps_are_on_the_song_timeline(self):
        s, _, _ = self.svc()
        st = wait_done(s, submit(s, self.wav10, {'language': 'en', 'clip_start': '4', 'clip_end': '9'}).id)    # clip holds sound 5-8 -> clip 1-4
        self.assertEqual(len(st['segments']), 1)
        self.assertAlmostEqual(st['segments'][0]['start'], 5.0, delta=0.25); self.assertAlmostEqual(st['segments'][0]['end'], 8.0, delta=0.25)
        self.assertEqual(st['clip'], {'start': 4.0, 'end': 9.0})

    def test_engine_failure_is_reported_and_cleaned(self):
        s, cfg, _ = self.svc(fail_on='transcribe')
        st = wait_done(s, submit(s, self.wav10, {'language': 'bn'}).id)
        self.assertEqual(st['status'], 'failed'); self.assertEqual(st['error']['code'], 'transcription_failed'); self.assertIn('simulated engine failure', st['error']['message'])
        self.assertNotIn('segments', st); self.assertEqual(leftover(cfg), [])

    def test_instrumental_audio_gives_warning_not_crash(self):
        s, _, _ = self.svc()
        silent = os.path.join(self.d, 'silent.wav')
        subprocess_run = __import__('subprocess').run
        subprocess_run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', 'anullsrc=r=16000:cl=mono', '-t', '12', silent], check=True)
        st = wait_done(s, submit(s, silent, {'language': 'en'}).id)
        self.assertEqual(st['status'], 'completed'); self.assertEqual(st['segments'], [])
        self.assertTrue(any('No sung or spoken words' in w for w in st['warnings'])); self.assertEqual(st['instrumentals'], [{'start': 0.0, 'end': 12.0}])

    def test_cancel_running_job_stops_and_cleans(self):
        s, cfg, eng = self.svc(delay=0.4)
        long_ = make_audio(os.path.join(self.d, 'l.wav'), 120.0, 2.0, 2.0)
        job = submit(s, long_, {'language': 'en'})
        while s.get(job.id)['stage'] != 'transcribing': time.sleep(0.02)
        time.sleep(0.6)
        self.assertEqual(s.delete(job.id)['status'], 'cancelled')
        t0 = time.time()
        while s.manager.get(job.id) and s.manager.get(job.id).status == 'running' and time.time() - t0 < 10: time.sleep(0.05)
        t0 = time.time()
        while leftover(cfg) and time.time() - t0 < 10: time.sleep(0.05)
        self.assertEqual(leftover(cfg), [])
        self.assertLess(len([c for c in eng.calls if c[0] == 'transcribe']), 2)      # it did not keep working through the whole file
        with self.assertRaises(ApiError) as e: s.get(job.id)
        self.assertEqual(e.exception.status, 404)

    def test_delete_unknown_and_delete_completed(self):
        s, _, _ = self.svc()
        with self.assertRaises(ApiError) as e: s.delete('0' * 32)
        self.assertEqual(e.exception.status, 404)
        job = submit(s, self.wav10, {'language': 'en'}); wait_done(s, job.id)
        self.assertEqual(s.delete(job.id)['status'], 'deleted')
        with self.assertRaises(ApiError): s.get(job.id)

    def test_timeout(self):
        s, cfg, _ = self.svc(delay=0.5, job_timeout_s=1)
        long_ = make_audio(os.path.join(self.d, 'l2.wav'), 60.0, 2.0, 2.0)
        st = wait_done(s, submit(s, long_, {'language': 'en'}).id)
        self.assertEqual((st['status'], st['error']['code']), ('failed', 'timeout')); self.assertEqual(leftover(cfg), [])

    def test_result_expires_after_ttl(self):
        s, cfg, _ = self.svc(job_ttl_s=0)
        job = submit(s, self.wav10, {'language': 'en'}); wait_done(s, job.id)
        time.sleep(0.05); s.manager.reap()
        with self.assertRaises(ApiError) as e: s.get(job.id)
        self.assertEqual(e.exception.status, 404)

    def test_orphan_temp_folders_removed_at_start(self):
        s, cfg, _ = make_service()
        os.makedirs(os.path.join(cfg.tmp_root, 'job-crashed')); _w(os.path.join(cfg.tmp_root, 'job-crashed', 'a.wav'), b'x')
        s.shutdown()
        from lyravox_ai.service import Service
        s2 = Service(cfg, FakeTestTranscriber(cfg)); self.svcs.append(s2)
        self.assertEqual(leftover(cfg), [])


class LimitTests(Base):
    def test_queue_limit_and_per_client_limit(self):
        s, cfg, _ = self.svc(delay=0.3, max_concurrent_jobs=1, max_queue=3, max_active_per_ip=2)
        p = make_audio(os.path.join(self.d, 'q.wav'), 20.0, 2.0, 2.0)
        a = submit(s, p, {}, 'A'); b = submit(s, p, {}, 'A')
        with self.assertRaises(ApiError) as e: submit(s, p, {}, 'A')
        self.assertEqual((e.exception.status, e.exception.code), (429, 'too_many_jobs'))
        c = submit(s, p, {}, 'B')
        with self.assertRaises(ApiError) as e: submit(s, p, {}, 'C')
        self.assertEqual((e.exception.status, e.exception.code), (503, 'server_busy'))
        self.assertEqual(leftover(cfg).__len__(), 3)                         # only the three admitted jobs hold temp files
        for j in (a, b, c): s.delete(j.id)

    def test_concurrent_submissions_are_admitted_exactly_up_to_the_limit(self):
        s, cfg, _ = self.svc(delay=0.2, max_concurrent_jobs=1, max_queue=5, max_active_per_ip=100)
        p = make_audio(os.path.join(self.d, 'r.wav'), 12.0, 2.0, 2.0)
        ok, busy, other = [], [], []
        def go(i):
            try: ok.append(submit(s, p, {}, f'c{i}'))
            except ApiError as e: busy.append(e.status)
            except Exception as e: other.append(e)
        ts = [threading.Thread(target=go, args=(i,)) for i in range(20)]
        [t.start() for t in ts]; [t.join() for t in ts]
        self.assertEqual(other, [])
        self.assertEqual((len(ok), len(busy)), (5, 15)); self.assertTrue(all(x == 503 for x in busy))
        for j in ok: s.delete(j.id)
        t0 = time.time()
        while leftover(cfg) and time.time() - t0 < 15: time.sleep(0.05)
        self.assertEqual(leftover(cfg), [])

    def test_never_more_than_max_concurrent_jobs_run_at_once(self):
        s, cfg, eng = self.svc(max_concurrent_jobs=2, max_queue=10, max_active_per_ip=100)
        live, peak, lock = [0], [0], threading.Lock()
        orig = eng.transcribe
        def tracked(*a, **k):
            with lock: live[0] += 1; peak[0] = max(peak[0], live[0])
            try:
                time.sleep(0.3); yield from orig(*a, **k)
            finally:
                with lock: live[0] -= 1
        eng.transcribe = tracked
        jobs = [submit(s, self.wav10, {'language': 'en'}, f'c{i}') for i in range(6)]
        for j in jobs: self.assertEqual(wait_done(s, j.id)['status'], 'completed')
        self.assertEqual(peak[0], 2)


class SeparationTests(Base):
    class Stub:
        def __init__(self, mode): self.mode = mode
        def available(self): return self.mode != 'missing'
        def separate(self, src, outdir, on_progress=None, cancel=None, deadline=None):
            if self.mode == 'fail': raise AudioError('Vocal separation failed: simulated')
            os.makedirs(outdir, exist_ok=True); out = os.path.join(outdir, 'vocals.wav'); shutil.copy(src, out)         # MOCK: "vocals" = the input
            if on_progress: on_progress(1.0)
            return out

    def run_with(self, mode):
        s, cfg, eng = self.svc(); s.separator = self.Stub(mode); s.manager.ctx.separator = s.separator
        return wait_done(s, submit(s, self.wav10, {'language': 'en', 'vocal_separation': 'true'}).id), cfg

    def test_separation_used_when_available_MOCK_SEPARATOR(self):
        st, cfg = self.run_with('ok')
        self.assertEqual(st['status'], 'completed'); self.assertEqual(st['vocal_separation'], {'requested': True, 'used': True, 'error': None}); self.assertEqual(leftover(cfg), [])

    def test_falls_back_to_original_audio_when_separation_fails(self):
        st, cfg = self.run_with('fail')
        self.assertEqual(st['status'], 'completed'); self.assertFalse(st['vocal_separation']['used']); self.assertIn('simulated', st['vocal_separation']['error'])
        self.assertTrue(any('original audio was used' in w for w in st['warnings'])); self.assertEqual(len(st['segments']), 2)

    def test_falls_back_when_separation_not_installed(self):
        st, _ = self.run_with('missing')
        self.assertEqual(st['status'], 'completed'); self.assertFalse(st['vocal_separation']['used']); self.assertIn('not available', st['vocal_separation']['error'])

    def test_real_demucs_class_reports_unavailable_without_package(self):
        from lyravox_ai.engines import DemucsSeparator
        from lyravox_ai.config import Config
        d = DemucsSeparator(Config())
        self.assertEqual(d.available(), DemucsSeparator.installed())


class LongAudioTests(Base):
    def test_25_minute_audio_is_chunked_in_order_with_bounded_memory(self):
        s, cfg, eng = self.svc(max_duration_s=2000, chunk_s=300)
        long_ = os.path.join(self.d, 'long.wav')
        make_audio(long_, 1500.0, 6.0, 4.0)                               # 25 min: 6 s of sound, 4 s of silence, repeating
        rss0 = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        t0 = time.time()
        job = submit(s, long_, {'language': 'en'})
        st = wait_done(s, job.id, timeout=180)
        self.assertEqual(st['status'], 'completed', st.get('error'))
        self.assertGreaterEqual(st['chunks'], 5)
        offsets = [c[3] for c in eng.calls if c[0] == 'transcribe']
        self.assertEqual(offsets, sorted(offsets)); self.assertEqual(offsets[0], 0.0)
        segs = st['segments']
        self.assertGreaterEqual(len(segs), 140)                            # ~150 sound stretches across 25 minutes
        self.assertEqual([x['start'] for x in segs], sorted(x['start'] for x in segs))
        self.assertAlmostEqual(segs[-1]['end'], 1500.0 - 4.0, delta=1.5)   # last sound stretch ends 4 s before the end
        # every chunk cut is in a silence, so no tone burst is split: segments never straddle a chunk boundary
        starts = [b for b in (c[3] for c in eng.calls if c[0] == 'transcribe')][1:]
        for b in starts:
            self.assertFalse(any(x['start'] < b < x['end'] for x in segs), f'a line straddles the chunk cut at {b}')
        self.assertEqual(leftover(cfg), [])
        grown_mb = (resource.getrusage(resource.RUSAGE_SELF).ru_maxrss - rss0) / 1024
        self.assertLess(grown_mb, 300, f'memory grew by {grown_mb:.0f} MB')
        print(f'\n   [long audio] 25 min, {st["chunks"]} chunks, {len(segs)} lines, {time.time() - t0:.1f} s, +{grown_mb:.0f} MB RSS')


class HealthTests(Base):
    def test_health_reports_limits_and_queue(self):
        s, cfg, _ = self.svc()
        h = s.health()
        self.assertEqual(h['limits']['max_upload_mb'], cfg.max_upload_mb); self.assertEqual(h['languages'], ['bn', 'en', 'hi'])
        self.assertIn('vocal_separation_available', h); self.assertEqual(h['formats'], ['.mp3', '.wav', '.m4a', '.aac', '.ogg'])


if __name__ == '__main__':
    unittest.main()
