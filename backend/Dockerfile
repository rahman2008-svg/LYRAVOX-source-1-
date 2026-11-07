# LYRAVOX AI backend for Render (or any Docker host).
#   docker build -t lyravox-ai backend --build-arg WHISPER_MODEL=base
#   docker run -p 8000:8000 -e ALLOWED_ORIGINS=* lyravox-ai
FROM python:3.11-slim

ARG WHISPER_MODEL=base
ARG INSTALL_DEMUCS=0
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 WHISPER_MODEL=${WHISPER_MODEL} WHISPER_CACHE=/models HF_HOME=/models/hf

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt requirements-demucs.txt ./
RUN pip install -r requirements.txt
RUN if [ "$INSTALL_DEMUCS" = "1" ]; then pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu && pip install -r requirements-demucs.txt; fi

# download the model into the image so the first request does not wait for it (and the service works without outbound access at run time)
RUN mkdir -p /models && python -c "import os; from faster_whisper import WhisperModel; WhisperModel(os.environ['WHISPER_MODEL'], device='cpu', compute_type='int8', download_root='/models')"

COPY lyravox_ai ./lyravox_ai
RUN useradd -m app && chown -R app /models /app
USER app
EXPOSE 8000
CMD ["sh", "-c", "uvicorn lyravox_ai.api:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
