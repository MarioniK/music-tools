# Roadmap 3.8 finalization-readiness modern TensorFlow runtime candidate.
# Non-production only: build explicitly with `docker build -f`.
# This file does not replace the production Dockerfile or docker-compose.yml.

ARG PYTHON_BASE_IMAGE=python:3.12.13-slim-bookworm@sha256:58525e1a8dada8e72d6f8a11a0ddff8d981fd888549108db52455d577f927f77
FROM ${PYTHON_BASE_IMAGE}

LABEL org.opencontainers.image.title="genre-classifier Roadmap 3.8 Python 3.12 essentia-tensorflow runtime candidate"
LABEL org.opencontainers.image.description="Non-production reproducible candidate for Python 3.12 + essentia-tensorflow validation"
LABEL org.opencontainers.image.stage="runtime-candidate"

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    ffmpeg \
    libgomp1 \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

COPY docker/runtime-candidates/py312-essentia-tensorflow/requirements.runtime.txt /app/requirements.runtime.txt

# Do not run pip install --upgrade pip/setuptools/wheel here. Roadmap 3.8
# keeps runtime packages fully pinned and records inherited/installed packaging
# tooling as evidence during validation.
RUN python -m pip install --no-cache-dir --requirement /app/requirements.runtime.txt

COPY app /app/app

EXPOSE 8021

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8021"]
