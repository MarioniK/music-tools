# Roadmap 3.8 Python 3.12 essentia-tensorflow runtime candidate

This directory contains a non-production runtime candidate for `genre-classifier`.
It exists only to iterate on the Python 3.12 + `essentia-tensorflow` path that Roadmap 3.5 and 3.6 validated.

This is not a production migration, provider switch, canary rollout, LLM cutover, or production runtime change. The production `Dockerfile`, `docker-compose.yml`, `requirements.txt`, app code, provider default, `/classify` contract, and response shape remain unchanged.

## Artifact

- `Dockerfile`
- `requirements.runtime.txt`
- `README.md`

Build from `/opt/music-tools/genre-classifier` only:

```sh
docker build \
  --no-cache \
  -f docker/runtime-candidates/py312-essentia-tensorflow/Dockerfile \
  -t music-tools-genre-classifier-roadmap-3.8:py312-etf \
  .
```

This image is intentionally not connected to the production `docker-compose.yml`.

## Base image strategy

Default base image:

```text
python:3.12.13-slim-bookworm@sha256:58525e1a8dada8e72d6f8a11a0ddff8d981fd888549108db52455d577f927f77
```

Roadmap 3.6 observed this digest for `python:3.12.13-slim-bookworm`. Roadmap 3.8 uses it as the default candidate base so rebuilds do not float with the tag.

The base can still be overridden for explicit future candidate experiments:

```sh
docker build \
  --build-arg PYTHON_BASE_IMAGE=python:3.12.13-slim-bookworm@sha256:<new-validated-digest> \
  -f docker/runtime-candidates/py312-essentia-tensorflow/Dockerfile \
  -t music-tools-genre-classifier-roadmap-3.8:py312-etf \
  .
```

## OS runtime dependencies

The candidate installs only the runtime OS packages required by the current service path:

- `ca-certificates`
- `ffmpeg`
- `libgomp1`
- `libsndfile1`

## Python dependency and tooling strategy

`requirements.runtime.txt` pins the full package set observed in Roadmap 3.6 `pip freeze`, including direct runtime dependencies and resolver-selected transitive dependencies. These pins stay isolated in the candidate artifact and must not be copied into production `requirements.txt`.

The Dockerfile does not run `pip install --upgrade pip setuptools wheel`. `pip` is inherited from the digest-pinned Python base image. `setuptools` and `wheel` are installed only through pinned package requirements and are recorded in validation evidence.

Required resolver evidence:

```sh
docker run --rm music-tools-genre-classifier-roadmap-3.8:py312-etf python --version
docker run --rm music-tools-genre-classifier-roadmap-3.8:py312-etf python -m pip --version
docker run --rm music-tools-genre-classifier-roadmap-3.8:py312-etf python -m pip freeze
docker run --rm music-tools-genre-classifier-roadmap-3.8:py312-etf python -m pip check
```

## Smoke commands

Start the candidate on an isolated host port:

```sh
docker run -d \
  --name genre-classifier-roadmap-3.8-candidate \
  -p 8521:8021 \
  music-tools-genre-classifier-roadmap-3.8:py312-etf
```

Run API smoke from `/opt/music-tools/genre-classifier`:

```sh
curl -fsS http://127.0.0.1:8521/health
curl -fsS -F "file=@app/tmp/upload.mp3" http://127.0.0.1:8521/classify
```

Run import and algorithm smoke:

```sh
docker run --rm music-tools-genre-classifier-roadmap-3.8:py312-etf \
  python -c "import essentia, essentia.standard as es; print(hasattr(es, 'MonoLoader')); print(hasattr(es, 'TensorflowPredictMusiCNN')); import app.main; import app.services.classify"
```

## Known risks

- Roadmap 3.6 found a TensorFlow-first import-order crash: importing `tensorflow` before `essentia` or the app failed with duplicate op registration for `Bitcast`.
- Roadmap 3.8 must revalidate whether this remains a supported import-order caveat or a blocker.
- The candidate uses TensorFlow 2.x and modern transitive dependencies while production remains on the existing legacy runtime.
- Fixture coverage is still local and small unless explicitly expanded in later roadmap work.
- Short smoke timing and memory evidence are not long-running stability evidence.

## Rollback baseline

Rollback baseline remains the current production service runtime:

- production Dockerfile: `Dockerfile`
- production compose: `docker-compose.yml`
- production requirements: `requirements.txt`
- default provider: `legacy_musicnn`
- production `/classify` contract and response shape unchanged

No production rollback command is required for this candidate stage because the production runtime is not modified.
