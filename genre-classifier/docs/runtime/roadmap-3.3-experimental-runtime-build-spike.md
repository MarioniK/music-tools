# Roadmap 3.3 — Experimental runtime build spike

## Status

Completed as an experimental evidence stage for `genre-classifier`.

Decision: **direct production runtime modernization is blocked**.

Roadmap 3.3 does not approve production runtime migration. It does not approve Python 3.7, Python 3.10, or Python 3.11 as a production runtime. It does not approve provider switch, canary rollout, LLM cutover, or LLM production adoption.

All three experimental images built successfully after the Python 3.7 Debian archive workaround, but none of the tested images are viable as current production-equivalent runtime replacements.

Shared blocker: pip-installed Essentia `2.1-beta6-dev` does not expose `TensorflowPredictMusiCNN` in any tested candidate. Because `app.services.classify` imports `TensorflowPredictMusiCNN` at module import time, `app.main` and `app.services.classify` fail to import before API startup. `/health` and `/classify` smoke tests were therefore blocked and not executed.

Successful Docker build is not sufficient runtime compatibility evidence. Successful TensorFlow import is not sufficient MusiCNN compatibility evidence.

## Service

`genre-classifier` only.

Repository areas outside this service, including `tidal-parser`, are out of scope and were not touched.

## Goal

Create isolated, non-production experimental Docker build artifacts for Python/runtime modernization evidence collection.

The goal was to gather build, dependency resolver, import, Essentia, MusiCNN model loading, ffmpeg, API, response shape, provider parity, shadow parity, and log evidence without touching the current production runtime path.

## Scope

- Add isolated experimental Dockerfiles under `docker/experimental/`.
- Keep production Dockerfile, `docker-compose.yml`, and `requirements.txt` unchanged.
- Copy the current service code into experimental images without modifying app code.
- Install experimental dependencies inside the experimental Dockerfiles only.
- Build experimental images explicitly with `docker build -f`.
- Treat failed builds or failed smoke checks as valid Roadmap 3.3 evidence.
- Use this stage only to decide whether deeper validation is warranted in Roadmap 3.4.

## Non-goals

- No production Python upgrade.
- No production Docker/base image replacement.
- No production dependency upgrade.
- No change to production `Dockerfile`.
- No change to production `docker-compose.yml`.
- No change to production `requirements.txt`.
- No app code changes.
- No provider default change.
- No `/classify` contract change.
- No response shape change.
- No canary rollout.
- No LLM cutover.
- No LLM production adoption decision.
- No provider promotion.
- No changes to `tidal-parser`.
- No commit, tag, or push.

## Production rollback baseline

Rollback baseline remains the current production runtime:

- Python: 3.6.9
- container OS: Ubuntu 18.04.3 LTS
- base image: `mtgupf/essentia-tensorflow:latest`
- TensorFlow: 1.15.0
- Essentia: 2.1-beta6-dev
- numpy: 1.19.5
- protobuf: 3.11.3
- h5py: 2.10.0
- FastAPI: 0.83.0
- Pydantic: 1.9.2
- Uvicorn: 0.16.0

Production behavior remains unchanged:

- default provider remains `legacy_musicnn`
- production response remains legacy-only
- `/classify` contract unchanged
- response shape unchanged
- shadow disabled by default
- no canary rollout
- no LLM cutover

Git and production safety evidence:

- branch: `roadmap-3.3-experimental-runtime-build-spike`
- HEAD: `d53a15a`, tag `v0.3.2`
- production `Dockerfile` unchanged
- production `docker-compose.yml` unchanged
- production `requirements.txt` unchanged
- app code unchanged
- `tidal-parser` untouched
- no commit, tag, or push performed

## Experimental runtime candidates

- Python 3.10: primary experimental target.
- Python 3.11: secondary experimental target with higher compatibility risk.
- Python 3.7: optional bridge experiment from Python 3.6.9; not a strategic modernization target.
- Python 3.12: deferred; no Dockerfile was added in Roadmap 3.3.

Python 3.10 and Python 3.11 experimental Dockerfiles intentionally install TensorFlow 2.12.1. This is a modern TensorFlow compatibility probe, not a production-equivalent TensorFlow 1.15 runtime.

A successful Python 3.10 or Python 3.11 build does not by itself prove compatibility with the legacy MusiCNN production path. The required blocker/evidence point is whether Essentia exposes a working `TensorflowPredictMusiCNN` implementation that can load and run the current frozen `.pb` model under that runtime.

If `TensorflowPredictMusiCNN` is absent or incompatible with TensorFlow 2.x, that is a valid MusiCNN compatibility blocker.

The Python 3.7 bridge image attempts to stay closer to the production TensorFlow 1.15-era stack. Python 3.7 is not a strategic target, and a successful Python 3.7 build can only be bridge evidence, not approval for production migration.

## Experimental build artifacts

Experimental Dockerfiles:

- `docker/experimental/python310/Dockerfile`
- `docker/experimental/python311/Dockerfile`
- `docker/experimental/python37/Dockerfile`

Experimental image tags:

- `music-tools-genre-classifier-roadmap-3.3:py310`
- `music-tools-genre-classifier-roadmap-3.3:py311`
- `music-tools-genre-classifier-roadmap-3.3:py37`

Evidence build commands:

```sh
docker build \
  -f docker/experimental/python310/Dockerfile \
  -t music-tools-genre-classifier-roadmap-3.3:py310 \
  .
```

```sh
docker build \
  -f docker/experimental/python311/Dockerfile \
  -t music-tools-genre-classifier-roadmap-3.3:py311 \
  .
```

```sh
docker build \
  -f docker/experimental/python37/Dockerfile \
  -t music-tools-genre-classifier-roadmap-3.3:py37 \
  .
```

The experimental images are intentionally built with `docker build -f`; they do not require changes to production `docker-compose.yml`.

## Build evidence

All three experimental images built successfully after the Python 3.7 Debian archive workaround.

Python 3.7 bridge initial build finding:

- initial `py37` build failed before dependency resolution
- failure stage: `apt-get update` / apt install
- failure reason: standard Debian buster repositories unavailable from default `deb.debian.org` locations
- mitigation: experimental `py37` Dockerfile changed to use `archive.debian.org` and `Acquire::Check-Valid-Until "false";`
- this is valid base OS lifecycle evidence
- production files unchanged

Python 3.7 repeated build:

- result: SUCCESS
- image: `sha256:13742d4886b857831da2e6e78de3752e528a721ecce48f0a80a6f7619ce6bcfd`
- created: `2026-05-02T00:36:39+03:00`
- size: `1926747601`

Python 3.10 build:

- result: SUCCESS
- image: `sha256:734ce4ff02add6384566fd1793d59981b156cdd1d1170d1404d370d4ef2abd7b`
- created: `2026-05-02T00:48:37+03:00`
- size: `2893214693`

Python 3.11 build:

- result: SUCCESS
- image: `sha256:fa412535c9ec68ac1ee87beafa629cf141c085f593d97f5d3d2320084fe9f28e`
- created: `2026-05-02T00:57:29+03:00`
- size: `2941670146`

Build conclusion:

- Successful build is not sufficient runtime compatibility evidence.
- Python 3.7 proves the bridge image can be built from archived buster repositories, but this also records base OS lifecycle risk.
- Python 3.10 and Python 3.11 prove modern Python images can be built with TensorFlow 2.12.1 and pip-installed Essentia, but not legacy MusiCNN compatibility.

## Dependency resolver evidence

Python 3.7 dependency smoke:

- Python: 3.7.17
- pip: 24.0
- TensorFlow: 1.15.0
- Essentia: 2.1-beta6-dev
- numpy: 1.19.5
- protobuf: 3.11.3
- h5py: 2.10.0
- FastAPI: 0.83.0
- Pydantic: 1.10.26
- Uvicorn: 0.16.0

Python 3.10 dependency smoke:

- Python: 3.10.20
- pip: 26.1
- TensorFlow: 2.12.1
- Essentia: 2.1-beta6-dev
- numpy: 1.23.5
- protobuf: 3.20.3
- h5py: 3.8.0
- FastAPI: 0.83.0
- Pydantic: 1.10.26
- Uvicorn: 0.16.0

Python 3.11 dependency smoke:

- Python: 3.11.15
- pip: 26.1
- TensorFlow: 2.12.1
- Essentia: 2.1-beta6-dev
- numpy: 1.23.5
- protobuf: 3.20.3
- h5py: 3.8.0
- FastAPI: 0.83.0
- Pydantic: 1.10.26
- Uvicorn: 0.16.0

Dependency parity findings:

- Python 3.7 keeps TensorFlow 1.15.0, numpy 1.19.5, protobuf 3.11.3, h5py 2.10.0, FastAPI 0.83.0, and Uvicorn 0.16.0 aligned with production baseline, but Pydantic resolves to 1.10.26 instead of production baseline 1.9.2.
- Python 3.10 and Python 3.11 intentionally drift from production TensorFlow 1.15.0 to experimental TensorFlow 2.12.1.
- Python 3.10 and Python 3.11 also drift on numpy, protobuf, h5py, and Pydantic.
- Pydantic 1.10.26 differs from production baseline 1.9.2 in all tested images.

## Import smoke evidence

Python 3.7:

- `import tensorflow`: OK
- TensorFlow version: 1.15.0
- TensorFlow graph/session smoke: SUCCESS
- `tf.Graph`: available
- `tf.Session`: available
- `tf.GraphDef`: available
- `import app.main`: FAILED
- `import app.services.classify`: FAILED

Python 3.10:

- `import tensorflow`: OK
- TensorFlow version: 2.12.1
- `import app.main`: FAILED
- `import app.services.classify`: FAILED

Python 3.11:

- `import tensorflow`: OK
- TensorFlow version: 2.12.1
- `import app.main`: FAILED
- `import app.services.classify`: FAILED

Shared app import failure:

```text
ImportError: cannot import name 'TensorflowPredictMusiCNN' from 'essentia.standard'
```

Observed module paths:

- Python 3.7: `/usr/local/lib/python3.7/site-packages/essentia/standard.py`
- Python 3.10: `/usr/local/lib/python3.10/site-packages/essentia/standard.py`
- Python 3.11: `/usr/local/lib/python3.11/site-packages/essentia/standard.py`

Impact:

- `app.main` cannot import.
- `app.services.classify` cannot import.
- API startup is blocked before request handling.

Blocker type:

- import blocker
- Essentia blocker
- MusiCNN compatibility blocker
- TensorFlow major version parity risk for Python 3.10 and Python 3.11

## Essentia smoke evidence

Python 3.7:

- Essentia import: OK
- Essentia version: 2.1-beta6-dev
- `MonoLoader` available: True
- `TensorflowPredictMusiCNN` available: False

Python 3.10:

- Essentia import: OK
- Essentia version: 2.1-beta6-dev
- `MonoLoader` available: True
- `TensorflowPredictMusiCNN` available: False

Python 3.11:

- Essentia import: OK
- Essentia version: 2.1-beta6-dev
- `MonoLoader` available: True
- `TensorflowPredictMusiCNN` available: False

Essentia conclusion:

- pip-installed Essentia imports in all tested candidates.
- pip-installed Essentia does not expose the production-required `TensorflowPredictMusiCNN` algorithm in any tested candidate.
- This blocks app import before API startup.

## MusiCNN model loading evidence

MusiCNN model loading smoke could not execute in any tested candidate.

Reason:

- `TensorflowPredictMusiCNN` is missing from pip-installed `essentia.standard` across Python 3.7, Python 3.10, and Python 3.11.
- `app.services.classify` imports `TensorflowPredictMusiCNN` at module import time.
- App import fails before model loading code can run.

Evidence interpretation:

- Python 3.7 proves TensorFlow 1.15 graph/session primitives can exist in a bridge image, but not production-equivalent Essentia/MusiCNN behavior.
- Python 3.10 and Python 3.11 prove modern Python images can be built with TensorFlow 2.12.1 and Essentia import, but not legacy MusiCNN compatibility.
- Successful TensorFlow import is not sufficient MusiCNN compatibility evidence.
- Missing `TensorflowPredictMusiCNN` is a hard compatibility blocker for the current legacy MusiCNN production path.

## ffmpeg normalization evidence

Python 3.7:

- ffmpeg: `4.1.11-0+deb10u1`
- base: Debian 10 / buster archive
- ffmpeg smoke: SUCCESS

Python 3.10:

- ffmpeg: `5.1.8-0+deb12u1`
- base: Debian 12 / bookworm
- ffmpeg smoke: SUCCESS

Python 3.11:

- ffmpeg smoke: not separately recorded in the supplied evidence

ffmpeg conclusion:

- Python 3.7 and Python 3.10 ffmpeg smoke passed.
- ffmpeg is not the current Roadmap 3.3 blocker.
- API-level ffmpeg normalization through `/classify` was not executed because app import blocks API startup.

## API smoke evidence

API smoke was blocked and not executed for all tested candidates.

Reason:

- `app.main` cannot import because `app.services.classify` cannot import `TensorflowPredictMusiCNN` from `essentia.standard`.
- API startup fails before request handling.

Not executed:

- `/health` smoke
- `/classify` fixture smoke

## Response shape parity

Response shape parity is not testable in Roadmap 3.3 experimental images.

Reason:

- API startup is blocked by app import failure before `/classify` can be exercised.

The production response shape remains unchanged because app code and production runtime files were not changed.

## Provider and shadow parity

Provider and shadow parity are not testable through the experimental API because API startup is blocked.

No code or configuration change was made to provider defaults or shadow defaults:

- default provider remains `legacy_musicnn` in production code/config
- shadow remains disabled by default in production code/config
- no LLM provider enabled by default
- no shadow mode enabled by default
- no canary rollout
- no LLM cutover

## Logs review

Logs/evidence reviewed:

- Python 3.7 initial build failure at apt repository stage.
- Python 3.7 repeated build success after Debian archive workaround.
- Python 3.7 dependency smoke.
- Python 3.7 TensorFlow graph/session smoke.
- Python 3.7 Essentia availability smoke.
- Python 3.7 app import failure.
- Python 3.7 ffmpeg smoke.
- Python 3.10 build success.
- Python 3.10 dependency smoke.
- Python 3.10 Essentia availability smoke.
- Python 3.10 app import failure.
- Python 3.10 ffmpeg smoke.
- Python 3.11 build success.
- Python 3.11 dependency smoke.
- Python 3.11 Essentia availability smoke.
- Python 3.11 app import failure.

Primary repeated log finding:

```text
ImportError: cannot import name 'TensorflowPredictMusiCNN' from 'essentia.standard'
```

## Blockers

Roadmap 3.3 blockers:

- Base OS lifecycle blocker for the initial Python 3.7 build: standard Debian buster repositories unavailable from default `deb.debian.org` locations.
- Debian archive usage for Python 3.7 is reproducibility/security risk evidence.
- Dependency parity drift: Pydantic resolves to 1.10.26 instead of production baseline 1.9.2 in all tested images.
- Dependency parity drift: Python 3.10 and Python 3.11 use numpy 1.23.5, protobuf 3.20.3, and h5py 3.8.0 instead of production baseline numpy 1.19.5, protobuf 3.11.3, and h5py 2.10.0.
- TensorFlow major version drift for Python 3.10 and Python 3.11: production TensorFlow 1.15.0 versus experimental TensorFlow 2.12.1.
- Missing `TensorflowPredictMusiCNN` across Python 3.7, Python 3.10, and Python 3.11.
- App import failure across all candidates.
- MusiCNN model loading smoke blocked across all candidates.
- API startup blocked across all candidates.
- `/health` smoke blocked and not executed.
- `/classify` fixture smoke blocked and not executed.
- Response shape parity not testable because API startup is blocked.
- Provider/shadow parity not testable through API because API startup is blocked.

## Decision

Roadmap 3.3 does not approve production runtime migration.

Roadmap 3.3 does not approve Python 3.7, Python 3.10, or Python 3.11 as a production runtime.

Roadmap 3.3 does not approve provider switch, canary rollout, LLM cutover, or LLM production adoption.

Roadmap 3.3 finds that direct runtime modernization is blocked by Essentia/MusiCNN algorithm availability, specifically missing `TensorflowPredictMusiCNN` in pip-installed Essentia.

Current production runtime remains the authoritative rollback baseline.

Decision rationale:

- All three experimental images build, but none can import the current app.
- The current app imports `TensorflowPredictMusiCNN` at module import time.
- pip-installed Essentia does not expose `TensorflowPredictMusiCNN` in any tested candidate.
- API startup is blocked before `/health` or `/classify` can be tested.
- Python 3.7 bridge evidence does not reproduce production-equivalent Essentia/MusiCNN behavior.
- Python 3.10 and Python 3.11 evidence does not prove legacy MusiCNN compatibility and includes TensorFlow major version drift.

## Recommendation for Roadmap 3.4

Focus on production runtime reproducibility and legacy runtime isolation before any Python upgrade:

- Pin or mirror the current production base image if possible.
- Document the production-only Essentia/TensorFlow capability as a hard dependency.
- Consider a lazy/import-safe boundary around Essentia and `TensorflowPredictMusiCNN` so incompatible runtimes fail diagnostically rather than killing app import.
- Add real runtime compatibility smoke tests for app import, `TensorflowPredictMusiCNN` availability, model loading, ffmpeg normalization, and `/health`.
- Do not pursue production Python 3.10/3.11 migration until the legacy MusiCNN runtime dependency is replaced, isolated, or reproduced.

Roadmap 3.4 should treat the current production image/runtime as the compatibility authority until a tested replacement reproduces the legacy MusiCNN algorithm path.

## Rollback considerations

Rollback remains the current production runtime and behavior.

Production files are unchanged:

- production `Dockerfile` unchanged
- production `docker-compose.yml` unchanged
- production `requirements.txt` unchanged
- app code unchanged

Experimental images are separate tags and are not used by production compose:

- `music-tools-genre-classifier-roadmap-3.3:py310`
- `music-tools-genre-classifier-roadmap-3.3:py311`
- `music-tools-genre-classifier-roadmap-3.3:py37`

No compose change, provider/default change, `/classify` contract change, response shape change, canary rollout, or LLM cutover was made.

Optional cleanup commands for experimental images:

```sh
docker image rm music-tools-genre-classifier-roadmap-3.3:py310
docker image rm music-tools-genre-classifier-roadmap-3.3:py311
docker image rm music-tools-genre-classifier-roadmap-3.3:py37
```

If image tags were retagged or dangling layers remain, inspect with:

```sh
docker images | grep 'music-tools-genre-classifier-roadmap-3.3'
docker image ls --filter dangling=true
```
