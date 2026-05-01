# Roadmap 3.3 experimental runtime build artifact.
# Non-production only: build explicitly with `docker build -f`.
# This file does not replace the production Dockerfile or docker-compose.yml.

FROM python:3.10-slim-bookworm

LABEL org.opencontainers.image.title="genre-classifier Roadmap 3.3 Python 3.10 experimental runtime"
LABEL org.opencontainers.image.description="Non-production evidence image for build/import/model/API smoke only"
LABEL org.opencontainers.image.stage="experimental"

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libgomp1 \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Keep the production requirements file available for evidence comparison, but do
# not edit it. Python 3.10 is expected to need experimental dependency resolution
# because production pins include numpy==1.19.5 and the legacy image supplies
# TensorFlow/Essentia out-of-band.
COPY requirements.txt /app/production-requirements.txt

RUN python -m pip install --no-cache-dir --upgrade pip setuptools wheel

# Experimental resolver input lives only in this Dockerfile/image. A failed
# resolver/build is valid Roadmap 3.3 evidence and must not be fixed by changing
# the production Dockerfile, docker-compose.yml, requirements.txt, or app code.
# TensorFlow 2.x is intentionally experimental here and does not match the
# production TensorFlow 1.15 runtime. MusiCNN / TensorflowPredictMusiCNN model
# loading smoke is required before considering this runtime viable.
RUN python -m pip install --no-cache-dir \
    fastapi==0.83.0 \
    uvicorn==0.16.0 \
    python-multipart==0.0.5 \
    jinja2==3.0.3 \
    numpy==1.23.5 \
    protobuf==3.20.3 \
    h5py==3.8.0 \
    tensorflow==2.12.1 \
    essentia

COPY app /app/app

EXPOSE 8021

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8021"]
