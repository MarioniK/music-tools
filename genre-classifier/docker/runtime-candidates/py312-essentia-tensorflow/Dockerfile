# Roadmap 3.6 reproducible modern TensorFlow runtime candidate.
# Non-production only: build explicitly with `docker build -f`.
# This file does not replace the production Dockerfile or docker-compose.yml.
#
# To freeze the base image digest after validation, build with:
#   --build-arg PYTHON_BASE_IMAGE=python:3.12.13-slim-bookworm@sha256:<digest>

ARG PYTHON_BASE_IMAGE=python:3.12.13-slim-bookworm
FROM ${PYTHON_BASE_IMAGE}

LABEL org.opencontainers.image.title="genre-classifier Roadmap 3.6 Python 3.12 essentia-tensorflow runtime candidate"
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

# Do not run an unpinned pip/setuptools/wheel upgrade here. Roadmap 3.6 keeps
# Python package runtime dependencies pinned and records inherited base-image
# packaging tooling as evidence during validation.
RUN python -m pip install --no-cache-dir -r /app/requirements.runtime.txt

COPY app /app/app

EXPOSE 8021

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8021"]
