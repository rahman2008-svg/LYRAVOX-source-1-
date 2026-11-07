"""Job manager: a bounded queue, a small worker pool, cancellation, timeouts, per-client limits, and cleanup of temp files / results."""
import os, shutil, threading, time, uuid
from concurrent.futures import ThreadPoolExecutor
from . import pipeline
from .errors import ApiError, AudioError, Cancelled, JobTimeout

ACTIVE = ('queued', 'running')


class Job:
    def __init__(self, workdir, src_path, params, client, info, timeout_s):
        self.id = uuid.uuid4().hex
        self.workdir, self.src_path, self.params, self.client, self.info = workdir, src_path, params, client, info
        self.status, self.stage, self.progress = 'queued', 'queued', 0.0
        self.created = self.updated = time.time()
        self.finished = None
        self.cancel = threading.Event()
        self.deadline = time.monotonic() + timeout_s + 3600        # real deadline starts when the job begins (see _run)
        self.timeout_s = timeout_s
        self.result, self.error = None, None
        self.discard = False                                        # DELETE was called: hide it, drop it when it stops
        self.extra = {}
        self._lock = threading.Lock()

    def set(self, **kw):
        with self._lock:
            for k in ('stage', 'status'):
                if k in kw: setattr(self, k, kw.pop(k))
            if 'progress' in kw:
                self.progress = max(self.progress, min(1.0, kw.pop('progress')))   # progress never goes backwards
            self.extra.update(kw)
            self.updated = time.time()

    def snapshot(self):
        with self._lock:
            d = {'job_id': self.id, 'status': self.status, 'stage': self.stage, 'progress': round(self.progress, 3),
                 'created': self.created, 'input': self.info}
            d.update({k: v for k, v in self.extra.items()})
            if self.status == 'completed' and self.result:
                d.update(self.result)
            if self.status in ('failed', 'cancelled') and self.error:
                d['error'] = self.error
            return d


class JobManager:
    def __init__(self, cfg, ctx):
        self.cfg, self.ctx = cfg, ctx
        self.jobs = {}
        self.lock = threading.Lock()
        self.pool = ThreadPoolExecutor(max_workers=cfg.max_concurrent_jobs, thread_name_prefix='lv-job')
        self._stop = threading.Event()
        os.makedirs(cfg.tmp_root, exist_ok=True)
        self._sweep_orphans()
        self.reaper = threading.Thread(target=self._reap_loop, daemon=True)
        self.reaper.start()

    # -- admission ------------------------------------------------------------------------------------------------------
    def new_workdir(self):
        d = os.path.join(self.cfg.tmp_root, 'job-' + uuid.uuid4().hex[:16])
        os.makedirs(d, exist_ok=True)
        return d

    def check_capacity(self, client):
        with self.lock:
            active = [j for j in self.jobs.values() if j.status in ACTIVE]
            if len(active) >= self.cfg.max_queue:
                raise ApiError(503, 'server_busy', 'The server is busy right now. Please try again in a few minutes.')
            if sum(1 for j in active if j.client == client) >= self.cfg.max_active_per_ip:
                raise ApiError(429, 'too_many_jobs', 'You already have the maximum number of unfinished jobs. Wait for one to finish or cancel it.')

    def submit(self, workdir, src_path, params, client, info):
        job = Job(workdir, src_path, params, client, info, self.cfg.job_timeout_s)
        with self.lock:
            active = [j for j in self.jobs.values() if j.status in ACTIVE]
            if len(active) >= self.cfg.max_queue:
                raise ApiError(503, 'server_busy', 'The server is busy right now. Please try again in a few minutes.')
            if sum(1 for j in active if j.client == client) >= self.cfg.max_active_per_ip:
                raise ApiError(429, 'too_many_jobs', 'You already have the maximum number of unfinished jobs. Wait for one to finish or cancel it.')
            self.jobs[job.id] = job                      # registered under the lock, so the capacity checks cannot be raced
        self.pool.submit(self._run, job)
        return job

    # -- execution ------------------------------------------------------------------------------------------------------
    def _run(self, job):
        status, error = 'completed', None
        try:
            if job.cancel.is_set():
                raise Cancelled()
            job.deadline = time.monotonic() + job.timeout_s
            job.set(status='running', stage='preparing')
            pipeline.run(job, self.ctx)
        except Cancelled:
            status = 'cancelled'
        except JobTimeout:
            status, error = 'failed', {'code': 'timeout', 'message': f'The job took longer than {job.timeout_s} s and was stopped. Try a shorter clip or a smaller model.'}
        except AudioError as e:
            status, error = 'failed', {'code': 'audio_error', 'message': str(e)}
        except MemoryError:
            status, error = 'failed', {'code': 'out_of_memory', 'message': 'The server ran out of memory. Try a shorter clip or a smaller model.'}
        except Exception as e:                           # engine / model errors: reported, never swallowed
            status, error = 'failed', {'code': 'transcription_failed', 'message': f'Transcription failed: {type(e).__name__}: {e}'[:400]}
        # the uploaded audio and every derived file are deleted BEFORE the final status is published, so a client that sees
        # "completed" can rely on nothing of its upload being left on the server
        shutil.rmtree(job.workdir, ignore_errors=True)
        self._finish(job, status, error)
        if job.discard:
            with self.lock:
                self.jobs.pop(job.id, None)

    def _finish(self, job, status, error):
        with job._lock:
            job.status, job.stage, job.error, job.finished = status, status, error, time.time()

    # -- queries --------------------------------------------------------------------------------------------------------
    def get(self, job_id):
        with self.lock:
            j = self.jobs.get(job_id)
            return None if (j is None or j.discard) else j

    def delete(self, job_id):
        """Cancel if still active, and forget the job. Returns the final status or None if unknown."""
        job = self.get(job_id)
        if job is None:
            return None
        job.cancel.set()
        job.discard = True
        if job.status in ACTIVE:
            # a job that never started is cancelled right away; a running one stops at its next check
            if job.status == 'queued':
                self._finish(job, 'cancelled', None)
                shutil.rmtree(job.workdir, ignore_errors=True)
        with self.lock:
            if job.status not in ACTIVE:
                self.jobs.pop(job_id, None)
        return job.status

    def active_count(self):
        with self.lock:
            return sum(1 for j in self.jobs.values() if j.status in ACTIVE)

    def running_count(self):
        with self.lock:
            return sum(1 for j in self.jobs.values() if j.status == 'running')

    # -- housekeeping ---------------------------------------------------------------------------------------------------
    def _sweep_orphans(self):
        """Temp folders left by a crashed process."""
        try:
            for n in os.listdir(self.cfg.tmp_root):
                p = os.path.join(self.cfg.tmp_root, n)
                if n.startswith('job-') and os.path.isdir(p):
                    shutil.rmtree(p, ignore_errors=True)
        except OSError:
            pass

    def reap(self):
        now = time.time()
        with self.lock:
            for jid, j in list(self.jobs.items()):
                if j.status not in ACTIVE and j.finished and now - j.finished > self.cfg.job_ttl_s:
                    del self.jobs[jid]
                elif j.status == 'queued' and now - j.created > self.cfg.job_timeout_s * 4:
                    j.cancel.set()

    def _reap_loop(self):
        while not self._stop.wait(30):
            self.reap()

    def shutdown(self):
        self._stop.set()
        for j in list(self.jobs.values()):
            j.cancel.set()
        self.pool.shutdown(wait=False, cancel_futures=True)
