# Roadmap 3.3 experimental runtime build artifact.
# Non-production only: build explicitly with `docker build -f`.
# Optional bridge experiment from Python 3.6.9; not a strategic target.
# This file does not replace the production Dockerfile or docker-compose.yml.

FROM python:3.7-slim-buster

LABEL org.opencontainers.image.title="genre-classifier Roadmap 3.3 Python 3.7 bridge experimental runtime"
LABEL org.opencontainers.image.description="Non-production bridge evidence image for build/import/model/API smoke only"
LABEL org.opencontainers.image.stage="experimental"

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Experimental bridge workaround only: python:3.7-slim-buster depends on an EOL
# Debian buster base whose standard repositories may no longer publish Release
# files. This is not a production runtime change. Using archive.debian.org is
# itself reproducibility/security risk evidence for Roadmap 3.3.
RUN printf '%s\n' \
    'deb http://archive.debian.org/debian buster main' \
    'deb http://archive.debian.org/debian buster-updates main' \
    'deb http://archive.debian.org/debian-security buster/updates main' \
    > /etc/apt/sources.list \
    && printf '%s\n' 'Acquire::Check-Valid-Until "false";' \
    > /etc/apt/apt.conf.d/99no-check-valid-until

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libgomp1 \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Python 3.7 is included only to test a bridge path close to the Python 3.6.9
# production baseline. It intentionally keeps the production app dependency pins,
# then adds legacy TensorFlow-era runtime inputs inside this experimental image.
COPY requirements.txt /app/production-requirements.txt

RUN python -m pip install --no-cache-dir --upgrade "pip<24.1" setuptools wheel
RUN python -m pip install --no-cache-dir -r /app/production-requirements.txt

# Essentia wheel availability for this bridge image is uncertain. A failed build
# or missing TensorflowPredictMusiCNN import is valid Roadmap 3.3 evidence.
# This is a bridge-only TensorFlow 1.15-era probe. Resolver conflicts are valid
# evidence; do not patch production requirements to make this build pass.
RUN python -m pip install --no-cache-dir \
    tensorflow==1.15.0 \
    protobuf==3.11.3 \
    h5py==2.10.0 \
    essentia

COPY app /app/app

EXPOSE 8021

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8021"]
