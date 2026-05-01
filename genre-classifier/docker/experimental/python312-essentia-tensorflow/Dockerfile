# Roadmap 3.4 experimental runtime compatibility artifact.
# Non-production only: build explicitly with `docker build -f`.
# This file does not replace the production Dockerfile or docker-compose.yml.

FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.title="genre-classifier Roadmap 3.4 Python 3.12 essentia-tensorflow experimental runtime"
LABEL org.opencontainers.image.description="Non-production evidence image for essentia-tensorflow build/import/model/API smoke only"
LABEL org.opencontainers.image.stage="experimental"

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libgomp1 \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Keep the production requirements file available for evidence comparison, but
# do not edit it. Roadmap 3.4 is a targeted package compatibility spike for
# essentia-tensorflow, not a production dependency migration.
COPY requirements.txt /app/production-requirements.txt

RUN python -m pip install --no-cache-dir --upgrade pip setuptools wheel

# Experimental resolver input lives only in this Dockerfile/image. A failed
# resolver/build is valid Roadmap 3.4 evidence and must not be fixed by changing
# the production Dockerfile, docker-compose.yml, requirements.txt, or app code.
#
# TensorFlow on Python 3.12 is intentionally experimental and does not match the
# production TensorFlow 1.15 runtime. The required evidence is whether this image
# exposes a working TensorflowPredictMusiCNN implementation that can load the
# current frozen MusiCNN .pb model and preserve API/response parity.
RUN python -m pip install --no-cache-dir \
    fastapi==0.83.0 \
    uvicorn==0.16.0 \
    python-multipart==0.0.5 \
    jinja2==3.0.3 \
    numpy \
    protobuf \
    h5py \
    tensorflow \
    essentia-tensorflow

COPY app /app/app

EXPOSE 8021

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8021"]
