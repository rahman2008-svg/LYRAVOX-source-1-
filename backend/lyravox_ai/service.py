"""Framework-independent service layer shared by the FastAPI app and the dev server: upload validation, job creation, queries, health.
Keeping the logic here means the HTTP frameworks stay thin adapters."""
import os, re, shutil, time
from . import __version__, audio
from .config import Config
from .engines import DemucsSeparator, FasterWhisperTranscriber
from .errors import ApiError, AudioError
from .jobs import JobManager
from .pipeline import Context

NAME_RE = re.compile(r'[^A-Za-z0-9._-]+')


class Service:
    def __init__(self, cfg=None, transcriber=None, separator=None):
        self.cfg = cfg or Config.from_env()
        self.transcriber = transcriber or FasterWhisperTranscriber(self.cfg)
        self.separator = separator or DemucsSeparator(self.cfg)
        self.manager = JobManager(self.cfg, Context(self.cfg, self.transcriber, self.separator))
        self.started = time.time()

    # ---------------------------------------------------------------------------------------------------------------------
    def health(self):
        c = self.cfg
        engine_ok = True if self.transcriber.name != 'faster-whisper' else FasterWhisperTranscriber.installed()
        return {'status': 'ok' if engine_ok else 'degraded', 'version': __version__, 'engine': self.transcriber.name, 'engine_available': engine_ok,
                'model': getattr(self.transcriber, 'model_name', ''), 'vocal_separation_available': bool(self.separator.available()),
                'languages': c.languages, 'limits': {'max_upload_mb': c.max_upload_mb, 'max_duration_s': c.max_duration_s, 'chunk_s': c.chunk_s,
                                                     'job_timeout_s': c.job_timeout_s},
                'queue': {'active': self.manager.active_count(), 'running': self.manager.running_count(), 'max': c.max_queue},
                'formats': list(audio.ALLOWED_EXT)}

    def parse_params(self, form):
        """Validate form fields (strings) into typed params. Raises ApiError(422)."""
        c = self.cfg
        lang = (form.get('language') or 'auto').strip().lower()
        if lang != 'auto' and lang not in c.languages:
            raise ApiError(422, 'unsupported_language', f"Language '{lang}' is not supported. Use 'auto' or one of: {', '.join(c.languages)}.")

        def b(name, default):
            v = form.get(name)
            if v is None or v == '': return default
            if str(v).strip().lower() in ('1', 'true', 'yes', 'on'): return True
            if str(v).strip().lower() in ('0', 'false', 'no', 'off'): return False
            raise ApiError(422, 'invalid_parameter', f"'{name}' must be true or false.")

        def f(name):
            v = form.get(name)
            if v is None or v == '': return None
            try:
                x = float(v)
            except ValueError:
                raise ApiError(422, 'invalid_parameter', f"'{name}' must be a number of seconds.")
            if x < 0 or x != x or x > 86400:
                raise ApiError(422, 'invalid_parameter', f"'{name}' is out of range.")
            return x
        p = {'language': lang, 'vocal_separation': b('vocal_separation', False), 'word_timestamps': b('word_timestamps', c.word_timestamps),
             'clip_start': f('clip_start'), 'clip_end': f('clip_end')}
        if p['clip_start'] is not None and p['clip_end'] is not None and p['clip_end'] - p['clip_start'] < 0.5:
            raise ApiError(422, 'invalid_parameter', "'clip_end' must be at least 0.5 s after 'clip_start'.")
        return p

    def create_job(self, filename, chunks, params, client, content_length=None):
        """chunks: iterator of bytes. Validates, stores the upload in a private temp folder, and queues the job."""
        c = self.cfg
        if content_length is not None and content_length > c.max_upload_bytes + 1_000_000:       # multipart overhead margin
            raise ApiError(413, 'file_too_large', f'The file is larger than the {c.max_upload_mb} MB limit.')
        ext = os.path.splitext(filename or '')[1].lower()
        if ext not in audio.ALLOWED_EXT:
            raise ApiError(415, 'unsupported_type', f"Unsupported audio type '{ext or 'unknown'}'. Use: {', '.join(audio.ALLOWED_EXT)}.")
        self.manager.check_capacity(client)               # fail early, before the upload is written to disk
        workdir = self.manager.new_workdir()
        keep = False
        try:
            src = os.path.join(workdir, 'input' + ext)
            size = 0
            with open(src, 'wb') as fh:
                for ch in chunks:
                    size += len(ch)
                    if size > c.max_upload_bytes:
                        raise ApiError(413, 'file_too_large', f'The file is larger than the {c.max_upload_mb} MB limit.')
                    fh.write(ch)
            if size == 0:
                raise ApiError(422, 'empty_file', 'The uploaded file is empty.')
            try:
                info = audio.probe(src)                   # content check: the extension alone proves nothing
            except AudioError as e:
                raise ApiError(422, 'invalid_audio', str(e))
            span = info['duration']
            cs, ce = params.get('clip_start'), params.get('clip_end')
            if cs is not None and cs >= info['duration']:
                raise ApiError(422, 'invalid_parameter', "'clip_start' is beyond the end of the audio.")
            if cs is not None or ce is not None:
                span = min(ce if ce is not None else info['duration'], info['duration']) - (cs or 0.0)
            if span > c.max_duration_s:
                raise ApiError(413, 'duration_exceeded', f'Audio is {span:.0f} s long; the limit is {c.max_duration_s} s. Send a shorter clip.')
            safe = NAME_RE.sub('_', os.path.basename(filename))[:80]
            job = self.manager.submit(workdir, src, params, client, {'filename': safe, 'size': size, 'duration': round(info['duration'], 2), 'codec': info['codec']})
            keep = True
            return job
        finally:
            if not keep:
                shutil.rmtree(workdir, ignore_errors=True)

    def get(self, job_id):
        j = self.manager.get(job_id)
        if j is None:
            raise ApiError(404, 'job_not_found', 'No such job (it may have expired or been deleted).')
        return j.snapshot()

    def delete(self, job_id):
        st = self.manager.delete(job_id)
        if st is None:
            raise ApiError(404, 'job_not_found', 'No such job (it may have expired or been deleted).')
        return {'job_id': job_id, 'status': 'cancelled' if st in ('queued', 'running', 'cancelled') else 'deleted'}

    def shutdown(self):
        self.manager.shutdown()
