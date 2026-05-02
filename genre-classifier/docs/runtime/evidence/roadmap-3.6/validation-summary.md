# Roadmap 3.6 validation summary

Validation date: 2026-05-02

Working directory: `/opt/music-tools/genre-classifier`

Branch: `roadmap-3.6-reproducible-runtime-candidate`

## Candidate build status

Status: pass

- image tag: `music-tools-genre-classifier-roadmap-3.6:py312-etf`
- image id: `sha256:174f0310d73fdf896beb753d58981e5465238a0060b89a56fa062556cc620d45`
- base image: `python:3.12.13-slim-bookworm`
- base digest observed during build: `sha256:58525e1a8dada8e72d6f8a11a0ddff8d981fd888549108db52455d577f927f77`
- build output: `candidate-build-output.txt`

## Runtime identity

- OS: Debian GNU/Linux 12 (bookworm)
- Python: `3.12.13`
- pip: `25.0.1`
- ffmpeg: `5.1.8-0+deb12u1`

Resolved package versions:

- TensorFlow: `2.21.0`
- Essentia package: `essentia-tensorflow==2.1b6.dev1389`
- numpy: `2.4.4`
- protobuf: `7.34.1`
- h5py: `3.14.0`
- FastAPI: `0.83.0`
- Pydantic: `1.10.26`
- Uvicorn: `0.16.0`
- Starlette: `0.19.1`
- python-multipart: `0.0.5`
- Jinja2: `3.0.3`

## Import and algorithm smoke

Combined import smoke status: fail

The combined import smoke printed `tensorflow 2.21.0`, then failed before reaching `essentia`, `essentia.standard`, `app.main`, or `app.services.classify`:

```text
F0000 ... Check failed: ... RegisterAlreadyLocked(op_data_factory) is OK (ALREADY_EXISTS: Op with name Bitcast)
```

Separate Essentia algorithm smoke status: pass

- `MonoLoader`: exists
- `TensorflowPredictMusiCNN`: exists
- `TensorflowPredictMusiCNN` import: pass

App import status from combined import smoke:

- `app.main`: not reached because the process failed earlier
- `app.services.classify`: not reached because the process failed earlier

API startup status still passed, which proves the service can import and run through its normal startup path when TensorFlow is not imported first by the smoke script.

## Model discovery

Status: pass

Found expected model files:

```text
/app/app/models/msd-musicnn-1.json
/app/app/models/msd-musicnn-1.pb
```

No candidate Dockerfile COPY change was required because production copies `app/`, and the model, template, static, and fixture files used by validation are inside `app/`.

## API health

- baseline `/health`: pass, `{"ok":true}`
- candidate `/health`: pass, `{"ok":true}`

## Primary classify parity

Fixture: `app/tmp/upload.mp3`

- baseline `/classify`: pass, HTTP success body with `ok: true`
- candidate `/classify`: pass, HTTP success body with `ok: true`
- baseline latency: `TIME_TOTAL:6.558106`
- candidate latency: `TIME_TOTAL:6.121977`

Top-level response keys:

- baseline: `ok`, `message`, `genres`, `genres_pretty`
- candidate: `ok`, `message`, `genres`, `genres_pretty`
- result: match

Top-1 genre:

- baseline: `electronic`
- candidate: `electronic`
- result: match

Genre sequence:

```text
electronic
indie
rock
indie rock
alternative
electro
pop
electronica
```

Result: exact match.

Score notes:

- baseline `rock`: `0.195`
- candidate `rock`: `0.1951`
- baseline `alternative`: `0.1556`
- candidate `alternative`: `0.1557`

Observed score drift is small and did not change genre ordering or response shape.

`genres_pretty`:

```text
indie rock
alternative rock
electronic
indie
rock
alternative
electro
pop
```

Result: exact match.

## Repeated request smoke

- baseline: 10/10 repeated `/classify` requests returned `ok: true`
- candidate: 10/10 repeated `/classify` requests returned `ok: true`

Baseline observed `TIME_TOTAL` range:

- min: `6.031403`
- max: `7.494609`

Candidate observed `TIME_TOTAL` range:

- min: `5.787881`
- max: `6.277141`

## Malformed and unsupported uploads

Fixtures:

- `empty.mp3`
- `fake.mp3`
- `unsupported.txt`

Baseline:

- `empty.mp3`: HTTP `400`, `{"ok":false,"error":"Файл пустой"}`
- `fake.mp3`: HTTP `400`, ffmpeg error body
- `unsupported.txt`: HTTP `400`, `{"ok":false,"error":"Неподдерживаемый формат файла"}`

Candidate:

- `empty.mp3`: HTTP `400`, `{"ok":false,"error":"Файл пустой"}`
- `fake.mp3`: HTTP `400`, ffmpeg error body
- `unsupported.txt`: HTTP `400`, `{"ok":false,"error":"Неподдерживаемый формат файла"}`

Result: status and error shape parity passed. ffmpeg version text differs, as expected from different OS/runtime images.

## Docker stats memory comparison

Captured with `docker stats --no-stream` after validation requests:

- baseline: `628.2MiB / 4GiB`, `15.34%`, PIDS `139`
- candidate: `387.8MiB / 4GiB`, `9.47%`, PIDS `9`

Result: candidate used less memory in this short validation smoke.

## Logs review summary

Baseline logs:

- startup completed
- Uvicorn running on `0.0.0.0:8021`
- `/health` returned `200`
- repeated `/classify` requests returned `200`
- malformed uploads returned `400`
- fake mp3 produced expected ffmpeg error log
- CUDA/GPU warnings were present

Candidate logs:

- startup completed
- Uvicorn running on `0.0.0.0:8021`
- `/health` returned `200`
- repeated `/classify` requests returned `200`
- malformed uploads returned `400`
- fake mp3 produced expected ffmpeg error log
- CUDA/GPU warnings were present

No API startup crash was observed in container logs.

## Blockers

Blocker: combined import smoke failed when `tensorflow` was imported before `essentia`.

Failure evidence:

```text
F0000 ... RegisterAlreadyLocked(op_data_factory) is OK (ALREADY_EXISTS: Op with name Bitcast)
```

Impact:

- normal API startup passed
- `TensorflowPredictMusiCNN` availability passed
- model discovery passed
- `/health` passed
- `/classify` parity passed for the primary fixture
- repeated request smoke passed
- malformed upload parity passed

This blocker prevents Roadmap 3.6 from being considered a clean pass for runtime switch planning without another candidate iteration or an explicit explanation of supported import order constraints.

## Decision

Decision: `needs_additional_runtime_candidate_iteration`

Production runtime migration is not approved by Roadmap 3.6.
