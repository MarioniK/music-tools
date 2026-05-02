# Roadmap 3.6 Python 3.12 essentia-tensorflow runtime candidate

This directory contains a non-production reproducible runtime candidate for `genre-classifier`.

It is not a production migration, provider switch, canary rollout, or LLM cutover. The production `Dockerfile`, production `docker-compose.yml`, production `requirements.txt`, app code, provider default, `/classify` contract, and response shape are intentionally unchanged.

## Artifact

- `Dockerfile`
- `requirements.runtime.txt`

Build from `/opt/music-tools/genre-classifier` only:

```sh
docker build \
  -f docker/runtime-candidates/py312-essentia-tensorflow/Dockerfile \
  -t music-tools-genre-classifier-roadmap-3.6:py312-etf \
  .
```

This image is intentionally not connected to the production `docker-compose.yml`.

## Base image strategy

Default base image:

```text
python:3.12.13-slim-bookworm
```

After validation, pin the image digest without changing the Dockerfile structure:

```sh
docker build \
  --build-arg PYTHON_BASE_IMAGE=python:3.12.13-slim-bookworm@sha256:<digest> \
  -f docker/runtime-candidates/py312-essentia-tensorflow/Dockerfile \
  -t music-tools-genre-classifier-roadmap-3.6:py312-etf \
  .
```

Digest evidence is pending validation.

## OS runtime dependencies

The candidate installs only the runtime OS packages required by the current service path:

- `ca-certificates`
- `ffmpeg`
- `libgomp1`
- `libsndfile1`

## Python dependency strategy

`requirements.runtime.txt` pins the Roadmap 3.5 confirmed modern runtime stack:

- `tensorflow==2.21.0`
- `essentia-tensorflow==2.1b6.dev1389`
- `numpy==2.4.4`
- `protobuf==7.34.1`
- `h5py==3.14.0`
- `fastapi==0.83.0`
- `pydantic==1.10.26`
- `uvicorn==0.16.0`
- `starlette==0.19.1`
- `python-multipart==0.0.5`
- `jinja2==3.0.3`

The Dockerfile does not run `pip install --upgrade pip setuptools wheel`. Packaging tooling is inherited from the selected Python base image and must be recorded during validation with:

```sh
docker run --rm music-tools-genre-classifier-roadmap-3.6:py312-etf python --version
docker run --rm music-tools-genre-classifier-roadmap-3.6:py312-etf python -m pip --version
docker run --rm music-tools-genre-classifier-roadmap-3.6:py312-etf python -m pip freeze
```

Tooling evidence is pending validation.

## Runtime behavior guardrails

The image starts the same ASGI app entrypoint as production:

```text
uvicorn app.main:app --host 0.0.0.0 --port 8021
```

Expected guardrails:

- default provider remains `legacy_musicnn`
- `/classify` contract remains unchanged
- success response shape remains `ok`, `message`, `genres`, `genres_pretty`
- runtime shadow remains disabled by default unless explicitly configured elsewhere

These guardrails must be revalidated before any Roadmap 3.7 recommendation.
