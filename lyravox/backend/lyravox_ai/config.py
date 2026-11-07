"""Configuration, read from environment variables (see backend/.env.example). No secrets are needed or used."""
import os, tempfile
from dataclasses import dataclass, field


def _int(name, default):
    try: return int(os.environ.get(name, default))
    except ValueError: return default


def _float(name, default):
    try: return float(os.environ.get(name, default))
    except ValueError: return default


def _bool(name, default):
    v = os.environ.get(name)
    return default if v is None else v.strip().lower() in ('1', 'true', 'yes', 'on')


def _list(name, default):
    return [x.strip() for x in os.environ.get(name, default).split(',') if x.strip()]


@dataclass
class Config:
    tmp_root: str = field(default_factory=lambda: os.path.join(tempfile.gettempdir(), 'lyravox-ai'))
    max_upload_mb: int = 50                 # uploaded file size limit
    max_duration_s: int = 900               # longest audio accepted (after any clip range)
    chunk_s: int = 300                      # long audio is transcribed in chunks of about this length, cut at silences
    max_concurrent_jobs: int = 1            # jobs running at the same time (each one is CPU / RAM heavy)
    max_queue: int = 6                      # jobs waiting + running; more are rejected with 503
    max_active_per_ip: int = 2              # unfinished jobs per client address
    job_timeout_s: int = 1800               # a job that runs longer is stopped
    job_ttl_s: int = 1800                   # finished results are forgotten after this long
    whisper_model: str = 'base'             # tiny / base / small / medium / large-v3 ... or a path
    whisper_device: str = 'cpu'
    whisper_compute: str = 'int8'
    whisper_beam: int = 5
    whisper_cache: str = ''                 # model download folder ('' = library default)
    languages: list = field(default_factory=lambda: ['bn', 'en', 'hi'])
    allowed_origins: list = field(default_factory=lambda: ['*'])
    demucs_enabled: bool = True             # allow vocal separation when the demucs package is installed
    demucs_model: str = 'htdemucs'
    demucs_timeout_s: int = 900
    word_timestamps: bool = True
    silence_db: float = -35.0
    silence_min_s: float = 0.6
    interlude_min_s: float = 6.0            # a gap this long between lyric lines is reported as instrumental

    @classmethod
    def from_env(cls):
        d = cls()
        d.tmp_root = os.environ.get('LYRAVOX_TMP', d.tmp_root)
        d.max_upload_mb = _int('MAX_UPLOAD_MB', d.max_upload_mb)
        d.max_duration_s = _int('MAX_DURATION_S', d.max_duration_s)
        d.chunk_s = max(30, _int('CHUNK_S', d.chunk_s))
        d.max_concurrent_jobs = max(1, _int('MAX_CONCURRENT_JOBS', d.max_concurrent_jobs))
        d.max_queue = max(1, _int('MAX_QUEUE', d.max_queue))
        d.max_active_per_ip = max(1, _int('MAX_ACTIVE_PER_IP', d.max_active_per_ip))
        d.job_timeout_s = _int('JOB_TIMEOUT_S', d.job_timeout_s)
        d.job_ttl_s = _int('JOB_TTL_S', d.job_ttl_s)
        d.whisper_model = os.environ.get('WHISPER_MODEL', d.whisper_model)
        d.whisper_device = os.environ.get('WHISPER_DEVICE', d.whisper_device)
        d.whisper_compute = os.environ.get('WHISPER_COMPUTE', d.whisper_compute)
        d.whisper_beam = _int('WHISPER_BEAM', d.whisper_beam)
        d.whisper_cache = os.environ.get('WHISPER_CACHE', d.whisper_cache)
        d.languages = _list('ALLOWED_LANGUAGES', ','.join(d.languages))
        d.allowed_origins = _list('ALLOWED_ORIGINS', '*')
        d.demucs_enabled = _bool('DEMUCS_ENABLED', d.demucs_enabled)
        d.demucs_model = os.environ.get('DEMUCS_MODEL', d.demucs_model)
        d.demucs_timeout_s = _int('DEMUCS_TIMEOUT_S', d.demucs_timeout_s)
        d.word_timestamps = _bool('WORD_TIMESTAMPS', d.word_timestamps)
        d.interlude_min_s = _float('INTERLUDE_MIN_S', d.interlude_min_s)
        return d

    @property
    def max_upload_bytes(self):
        return self.max_upload_mb * 1024 * 1024
