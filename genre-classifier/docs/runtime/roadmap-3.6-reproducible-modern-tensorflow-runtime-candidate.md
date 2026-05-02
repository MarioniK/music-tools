# Roadmap 3.6 - Reproducible modern TensorFlow runtime candidate

## Goal

Prepare and validate a separate reproducible modern TensorFlow runtime candidate artifact for `genre-classifier` based on the successful Roadmap 3.4 and Roadmap 3.5 Python 3.12 + `essentia-tensorflow` path.

This stage does not approve production migration.

## Scope

- `genre-classifier` only
- non-production runtime candidate artifact
- pinned candidate runtime dependency input
- build, resolver, import, model discovery, API smoke, parity, memory, and log evidence
- decision artifact update with factual Roadmap 3.6 validation results

Candidate artifact path:

```text
docker/runtime-candidates/py312-essentia-tensorflow/
```

Evidence path:

```text
docs/runtime/evidence/roadmap-3.6/
```

## Non-goals

- No `tidal-parser` changes.
- No production `Dockerfile` change.
- No production `docker-compose.yml` change.
- No production `requirements.txt` change.
- No app code change.
- No production runtime migration.
- No provider switch.
- No provider default change.
- No `/classify` contract change.
- No response shape change.
- No canary rollout.
- No LLM cutover.
- No candidate image wiring into production compose.
- No commit, tag, or push.

## Roadmap 3.5 findings summary

Roadmap 3.5 isolated runtime parity validation passed for deeper migration planning.

Summary of recorded Roadmap 3.5 findings:

- Baseline and candidate containers both started successfully.
- `/health` returned HTTP `200` for both runtimes.
- `/classify` returned HTTP `200` for the valid primary fixture on both runtimes.
- Success response shape remained `ok`, `message`, `genres`, `genres_pretty`.
- Top-N genre sequence matched exactly for the primary fixture.
- `genres_pretty` matched exactly for the primary fixture.
- Short repeated request smoke passed for both runtimes.
- Malformed upload behavior remained HTTP `400` and did not crash either runtime.
- Candidate memory during short smoke was lower than baseline in captured `docker stats` evidence.
- Logs showed no startup blocker or crash in the captured tail.

Roadmap 3.5 did not approve production migration. It identified dependency pinning and reproducible candidate image strategy as Roadmap 3.6 work.

## Current production rollback baseline

Production rollback baseline remains the current production service runtime:

- production Dockerfile: `Dockerfile`
- production compose: `docker-compose.yml`
- production requirements: `requirements.txt`
- base image observed during Roadmap 3.6 baseline build: `mtgupf/essentia-tensorflow:latest@sha256:43dbaf1507416167f2adeebc2cb9c6c657b65d38a967b6408487f48271b7b44b`
- baseline image id: `sha256:6ef15c1bdbeb6b82efef02045b9a68de309c41442860da00c635ffa061d3ab75`
- Python: `3.6.9` from previous runtime baseline evidence
- TensorFlow: `1.15.0` from previous runtime baseline evidence
- Essentia: `2.1-beta6-dev` from previous runtime baseline evidence
- numpy: `1.19.5` from production `requirements.txt`
- FastAPI: `0.83.0` from production `requirements.txt`
- Uvicorn: `0.16.0` from production `requirements.txt`

Production behavior baseline:

- default provider remains `legacy_musicnn`
- `/classify` contract unchanged
- response shape unchanged
- runtime shadow disabled by default

## Candidate runtime strategy

Candidate artifact:

```text
docker/runtime-candidates/py312-essentia-tensorflow/Dockerfile
docker/runtime-candidates/py312-essentia-tensorflow/requirements.runtime.txt
docker/runtime-candidates/py312-essentia-tensorflow/README.md
```

The candidate:

- uses a Python 3.12 base image strategy
- defaults to `python:3.12.13-slim-bookworm`
- installs minimal OS runtime dependencies: `ca-certificates`, `ffmpeg`, `libgomp1`, `libsndfile1`
- installs pinned Python runtime dependencies from `requirements.runtime.txt`
- copies the existing `app` package into `/app/app`
- starts `uvicorn app.main:app --host 0.0.0.0 --port 8021`
- is built explicitly with `docker build -f`
- is not connected to production compose

Production and candidate Dockerfile `COPY` review:

- production copies `requirements.txt` and `app/`
- candidate copies `requirements.runtime.txt` and `app/`
- model files are under `app/models/`
- validation fixture `upload.mp3` is under `app/tmp/`
- templates are under `app/templates/`
- static assets are under `app/static/`

No candidate Dockerfile COPY update was required.

## Dependency pinning strategy

Roadmap 3.6 converts the successful Roadmap 3.4 floating resolver output into explicit runtime pins:

```text
tensorflow==2.21.0
essentia-tensorflow==2.1b6.dev1389
numpy==2.4.4
protobuf==7.34.1
h5py==3.14.0
fastapi==0.83.0
pydantic==1.10.26
uvicorn==0.16.0
starlette==0.19.1
python-multipart==0.0.5
jinja2==3.0.3
```

The Dockerfile does not run an unpinned `pip`, `setuptools`, or `wheel` upgrade. Packaging tooling is inherited from the selected Python base image. Roadmap 3.6 observed:

- pip: `25.0.1`
- setuptools installed by dependency resolution: `82.0.1`
- wheel installed by dependency resolution: `0.47.0`

## Base image strategy

Default base:

```text
python:3.12.13-slim-bookworm
```

Observed base image digest during Roadmap 3.6 build:

```text
sha256:58525e1a8dada8e72d6f8a11a0ddff8d981fd888549108db52455d577f927f77
```

The Dockerfile supports digest pinning through `PYTHON_BASE_IMAGE`:

```sh
docker build \
  --build-arg PYTHON_BASE_IMAGE=python:3.12.13-slim-bookworm@sha256:<digest> \
  -f docker/runtime-candidates/py312-essentia-tensorflow/Dockerfile \
  -t music-tools-genre-classifier-roadmap-3.6:py312-etf \
  .
```

The default Dockerfile still uses the tag form; the observed digest is evidence for a future digest-pinned rebuild.

## Reproducible build evidence

Status: pass for candidate build

Command:

```sh
docker build \
  -f docker/runtime-candidates/py312-essentia-tensorflow/Dockerfile \
  -t music-tools-genre-classifier-roadmap-3.6:py312-etf \
  .
```

Evidence:

- candidate build output: `docs/runtime/evidence/roadmap-3.6/candidate-build-output.txt`
- candidate image inspect: `docs/runtime/evidence/roadmap-3.6/candidate-image-inspect.json`
- candidate image id: `sha256:174f0310d73fdf896beb753d58981e5465238a0060b89a56fa062556cc620d45`
- base digest observed: `sha256:58525e1a8dada8e72d6f8a11a0ddff8d981fd888549108db52455d577f927f77`

Repeated build comparison: not executed.

## Resolver evidence

Status: pass

Evidence:

- Python version: `docs/runtime/evidence/roadmap-3.6/candidate-python-version.txt`
- pip version: `docs/runtime/evidence/roadmap-3.6/candidate-pip-version.txt`
- pip freeze: `docs/runtime/evidence/roadmap-3.6/candidate-pip-freeze.txt`
- OS release: `docs/runtime/evidence/roadmap-3.6/candidate-os-release.txt`
- ffmpeg version: `docs/runtime/evidence/roadmap-3.6/candidate-ffmpeg-version.txt`

Observed identity:

- OS: Debian GNU/Linux 12 (bookworm)
- Python: `3.12.13`
- pip: `25.0.1`
- ffmpeg: `5.1.8-0+deb12u1`
- TensorFlow: `2.21.0`
- `essentia-tensorflow`: `2.1b6.dev1389`
- numpy: `2.4.4`
- protobuf: `7.34.1`
- h5py: `3.14.0`
- FastAPI: `0.83.0`
- Pydantic: `1.10.26`
- Uvicorn: `0.16.0`
- Starlette: `0.19.1`
- python-multipart: `0.0.5`
- Jinja2: `3.0.3`

## Import smoke evidence

Combined import smoke status: fail

Evidence:

- `docs/runtime/evidence/roadmap-3.6/candidate-import-smoke.txt`

The script printed `tensorflow 2.21.0`, then failed before reaching `essentia`, `essentia.standard`, `app.main`, or `app.services.classify`:

```text
F0000 ... Check failed: ... RegisterAlreadyLocked(op_data_factory) is OK (ALREADY_EXISTS: Op with name Bitcast)
```

Separate algorithm smoke status: pass

Evidence:

- `docs/runtime/evidence/roadmap-3.6/candidate-essentia-algorithms-smoke.txt`
- `docs/runtime/evidence/roadmap-3.6/candidate-musicnn-smoke.txt`

Observed:

- `MonoLoader`: `True`
- `TensorflowPredictMusiCNN`: `True`
- `TensorflowPredictMusiCNN` import: pass

`app.main` and `app.services.classify` were not reached in the combined import smoke because the process failed earlier. Normal API startup still passed and therefore validated the app through the service startup path.

## Image digest evidence

Status: partially captured

Captured:

- base image digest observed during build: `sha256:58525e1a8dada8e72d6f8a11a0ddff8d981fd888549108db52455d577f927f77`
- candidate image id: `sha256:174f0310d73fdf896beb753d58981e5465238a0060b89a56fa062556cc620d45`

Not captured:

- candidate registry repo digest, because the image was not pushed
- SBOM/package inventory beyond `pip freeze`

## Model discovery evidence

Status: pass

Evidence:

- `docs/runtime/evidence/roadmap-3.6/candidate-model-discovery.txt`

Found:

```text
/app/app/models/msd-musicnn-1.json
/app/app/models/msd-musicnn-1.pb
```

## Smoke evidence

Status: pass for API smoke

Evidence:

- candidate startup logs: `docs/runtime/evidence/roadmap-3.6/candidate-startup-logs-initial.txt`
- candidate health: `docs/runtime/evidence/roadmap-3.6/candidate-health.json`
- candidate primary classify: `docs/runtime/evidence/roadmap-3.6/candidate-classify-upload.txt`
- candidate malformed uploads: `docs/runtime/evidence/roadmap-3.6/candidate-malformed-uploads.txt`

Observed:

- candidate container startup: pass
- `/health`: `{"ok":true}`
- valid `/classify`: `ok: true`
- valid `/classify` `TIME_TOTAL`: `6.121977`
- malformed `empty.mp3`: HTTP `400`
- malformed `fake.mp3`: HTTP `400`
- unsupported `unsupported.txt`: HTTP `400`
- ffmpeg command exists and reports `5.1.8-0+deb12u1`

## Parity revalidation evidence

Status: pass for API parity, with import-smoke blocker noted separately

Evidence:

- baseline build output: `docs/runtime/evidence/roadmap-3.6/baseline-build-output.txt`
- baseline health: `docs/runtime/evidence/roadmap-3.6/baseline-health.json`
- candidate health: `docs/runtime/evidence/roadmap-3.6/candidate-health.json`
- baseline classify: `docs/runtime/evidence/roadmap-3.6/baseline-classify-upload.txt`
- candidate classify: `docs/runtime/evidence/roadmap-3.6/candidate-classify-upload.txt`
- baseline repeated classify: `docs/runtime/evidence/roadmap-3.6/baseline-repeated-classify.txt`
- candidate repeated classify: `docs/runtime/evidence/roadmap-3.6/candidate-repeated-classify.txt`
- malformed uploads: `baseline-malformed-uploads.txt`, `candidate-malformed-uploads.txt`
- structured summary: `docs/runtime/evidence/roadmap-3.6/validation-summary.md`

Observed parity:

- baseline `/health`: pass, `{"ok":true}`
- candidate `/health`: pass, `{"ok":true}`
- baseline `/classify`: pass, `ok: true`
- candidate `/classify`: pass, `ok: true`
- success top-level keys match: `ok`, `message`, `genres`, `genres_pretty`
- top-1 genre matches: `electronic`
- genre sequence matches exactly
- `genres_pretty` matches exactly
- repeated request smoke: baseline 10/10, candidate 10/10
- malformed upload statuses match: HTTP `400` for `empty.mp3`, `fake.mp3`, and `unsupported.txt`

Observed primary fixture timing:

- baseline `TIME_TOTAL`: `6.558106`
- candidate `TIME_TOTAL`: `6.121977`

Observed score differences:

- baseline `rock`: `0.195`
- candidate `rock`: `0.1951`
- baseline `alternative`: `0.1556`
- candidate `alternative`: `0.1557`

The score differences did not change ordering, top-1, genre sequence, `genres_pretty`, or response shape.

## Performance and memory evidence

Status: short smoke captured

Evidence:

- `docs/runtime/evidence/roadmap-3.6/docker-stats.txt`
- classify timing in `baseline-classify-upload.txt`, `candidate-classify-upload.txt`, `baseline-repeated-classify.txt`, and `candidate-repeated-classify.txt`

Observed memory after validation requests:

- baseline: `628.2MiB / 4GiB`, `15.34%`, PIDS `139`
- candidate: `387.8MiB / 4GiB`, `9.47%`, PIDS `9`

Repeated request timing:

- baseline min/max observed: `6.031403` / `7.494609`
- candidate min/max observed: `5.787881` / `6.277141`

This is short smoke evidence only, not long-running performance approval.

## Logs review

Status: reviewed

Evidence:

- `docs/runtime/evidence/roadmap-3.6/baseline-logs-tail-300.txt`
- `docs/runtime/evidence/roadmap-3.6/candidate-logs-tail-300.txt`

Baseline logs:

- startup completed
- Uvicorn running on `0.0.0.0:8021`
- `/health` returned `200`
- `/classify` returned `200` for valid uploads
- malformed uploads returned `400`
- fake mp3 produced expected ffmpeg error log
- CUDA/GPU warnings were present

Candidate logs:

- startup completed
- Uvicorn running on `0.0.0.0:8021`
- `/health` returned `200`
- `/classify` returned `200` for valid uploads
- malformed uploads returned `400`
- fake mp3 produced expected ffmpeg error log
- CUDA/GPU warnings were present

No API startup crash was observed in the validation container logs.

## Rollback strategy

Rollback remains simple because Roadmap 3.6 does not change production runtime wiring.

Rollback action:

- continue using the existing production `Dockerfile`, `docker-compose.yml`, and `requirements.txt`
- do not build or run the Roadmap 3.6 candidate for production traffic
- remove or ignore the candidate image if validation fails

No production rollback command is required for this stage because no production migration is performed.

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

This blocker prevents Roadmap 3.6 from being considered a clean pass for controlled runtime switch planning without another candidate iteration or an explicit explanation of supported import order constraints.

## Import-order compatibility finding

Additional import-order diagnostics were captured after the initial Roadmap 3.6 validation.

Evidence:

- `docs/runtime/evidence/roadmap-3.6/import-order-tensorflow-only.txt`
- `docs/runtime/evidence/roadmap-3.6/import-order-essentia-only.txt`
- `docs/runtime/evidence/roadmap-3.6/import-order-essentia-then-tensorflow.txt`
- `docs/runtime/evidence/roadmap-3.6/import-order-tensorflow-then-essentia.txt`
- `docs/runtime/evidence/roadmap-3.6/import-order-app-natural-path.txt`
- `docs/runtime/evidence/roadmap-3.6/import-order-tensorflow-before-app.txt`
- `docs/runtime/evidence/roadmap-3.6/import-order-essentia-before-app.txt`
- `docs/runtime/evidence/roadmap-3.6/import-order-diagnostic-summary.md`

Passing import orders:

- TensorFlow-only import passed and reported `tensorflow 2.21.0`.
- Essentia-only import passed and reported `essentia 2.1-beta6-dev`, `MonoLoader True`, and `TensorflowPredictMusiCNN True`.
- Essentia first, then TensorFlow passed and reported `tensorflow after essentia ok`.
- Natural app import path passed: `app.main natural import ok` and `app.services.classify natural import ok`.
- Essentia before app import passed.

Failing import orders:

- TensorFlow first, then Essentia failed.
- TensorFlow before app import failed.

Failure summary:

```text
F0000 ... RegisterAlreadyLocked(op_data_factory) is OK (ALREADY_EXISTS: Op with name Bitcast)
```

Production migration impact:

- Roadmap 3.6 still does not approve production runtime migration.
- The current production runtime path is unaffected because production Dockerfile, production compose, production requirements, provider default, `/classify` contract, response shape, and `tidal-parser` remain unchanged.
- The candidate API startup and `/classify` path remain compatible in the observed validation because the natural app import path passed and API parity evidence passed.

Decision impact:

- Decision remains `needs_additional_runtime_candidate_iteration`.
- The issue is narrower than a general API startup failure, but it is a real compatibility caveat for any environment or future code path that imports TensorFlow before Essentia/App code.
- Roadmap 3.7 should either resolve this import-order incompatibility or explicitly document the supported import order before any controlled runtime switch planning.

## Decision

Decision: `needs_additional_runtime_candidate_iteration`

Rationale:

- candidate build passed
- resolver evidence passed
- model discovery passed
- API startup and `/health` passed
- primary `/classify` and repeated request parity passed
- malformed upload parity passed
- short memory evidence was favorable for candidate
- combined import smoke failed with a TensorFlow/Essentia duplicate op registration crash

Production runtime migration is not approved by Roadmap 3.6.

Production safety statements:

- production Dockerfile remains unchanged
- production compose remains unchanged
- production requirements remains unchanged
- provider default remains `legacy_musicnn`
- `/classify` contract remains unchanged
- response shape remains unchanged
- `tidal-parser` remains untouched

## Recommendation for Roadmap 3.7

Roadmap 3.7 should perform an additional runtime candidate iteration before any controlled runtime switch planning:

- investigate the `tensorflow` before `essentia` import-order crash
- decide whether the candidate must support arbitrary import order or only the app's normal startup import path
- rerun combined import smoke after the candidate iteration
- rebuild from a digest-pinned `python:3.12.13-slim-bookworm` base
- repeat Roadmap 3.6 API parity checks
- expand fixture coverage beyond the current local primary fixture
- capture longer-running latency and memory evidence
- keep production Dockerfile, compose, requirements, provider default, `/classify` contract, and response shape unchanged until a separate migration decision exists
