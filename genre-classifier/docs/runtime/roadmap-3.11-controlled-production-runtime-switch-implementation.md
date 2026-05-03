# Roadmap 3.11 - Controlled production runtime switch implementation

## Goal

Implement and validate a controlled production runtime switch for `genre-classifier` from the legacy Python 3.6 / TensorFlow 1.15 runtime image to the validated Python 3.12 + `essentia-tensorflow` runtime candidate.

This stage changes runtime packaging only. It does not change application behavior.

## Scope

Allowed production changes:

- `Dockerfile`
- `requirements.txt`
- this decision artifact
- evidence under `docs/runtime/evidence/roadmap-3.11/`

Unchanged:

- `docker-compose.yml`
- `app/**`
- `tidal-parser/**`
- default provider
- `/classify` request contract
- response shape
- cache behavior
- LLM/canary settings

## Runtime decision

Production now uses the Roadmap 3.8 validated runtime design:

- Python `3.12.13`
- Debian bookworm slim base, digest-pinned
- TensorFlow `2.21.0`
- `essentia-tensorflow==2.1b6.dev1389`
- Essentia runtime identity expected as `2.1-beta6-dev`
- FastAPI `0.83.0`
- Pydantic `1.10.26`
- Uvicorn `0.16.0`

The production dependency input remains `requirements.txt` because the existing production Dockerfile already uses it. The candidate-only `docker/runtime-candidates/py312-essentia-tensorflow/requirements.runtime.txt` was used as the source for the promoted pins.

`docker-compose.yml` was not changed because it already builds the production Dockerfile with `build: .` and does not need runtime-specific wiring.

## Import-order invariant

The supported production path is app-first / Essentia-first.

TensorFlow-first mixed import paths are unsupported for this runtime candidate.

Duplicate `Bitcast` registration during normal startup or classify is a switch blocker and rollback trigger.

Supported import-order gates:

- `essentia_first`
- `essentia_standard_first`
- `classify_import`
- `app_main_import`
- `classify_then_tensorflow`
- `app_then_tensorflow`
- `model_load_essentia_first`
- `same_process_repeated_imports`

## Validation evidence

Evidence is stored under:

```text
docs/runtime/evidence/roadmap-3.11/
```

Required validation:

- clean production build
- production service start
- runtime identity
- `pip check`
- supported import-order smoke
- model load validation
- `/health`
- `/classify` fixture
- provider default and response shape check
- repeated classify smoke
- malformed/unsupported upload smoke
- logs review for `Bitcast`, `RegisterAlreadyLocked`, and tracebacks
- memory and latency sanity
- rollback readiness

Validation was run from:

```text
/opt/music-tools/genre-classifier
```

Production compose was used only for the `genre-classifier` service:

```sh
docker compose build
docker compose up -d genre-classifier
```

Observed runtime identity:

- Python `3.12.13`
- TensorFlow `2.21.0`
- `essentia-tensorflow==2.1b6.dev1389`
- Essentia `2.1-beta6-dev`
- ffmpeg `5.1.8-0+deb12u1`
- FastAPI `0.83.0`
- Pydantic `1.10.26`
- Uvicorn `0.16.0`

Observed container image id:

```text
sha256:2ccb366bd05e691821d82e1348efdbc65bbcae35a1f2c171134449e5802fb55d
```

Validation result:

- build passed
- service startup passed
- `/health` passed with `{"ok":true}`
- `/classify` fixture passed with HTTP `200`
- response shape remained `ok`, `message`, `genres`, `genres_pretty`
- provider default remained `legacy_musicnn`
- runtime shadow remained disabled
- `pip check` passed
- supported import-order smoke passed
- Essentia-first model load passed
- 10 repeated `/classify` requests passed
- malformed empty upload returned HTTP `400`
- malformed fake mp3 upload returned HTTP `400`
- unsupported text upload returned HTTP `400`
- service remained up after malformed upload checks
- logs contained no `Bitcast`, `RegisterAlreadyLocked`, traceback, or critical errors
- memory sanity after validation was `306MiB / 4GiB`
- repeated classify latency sanity: min `9.626306s`, max `12.872652s`, avg `10.353960s`

Known non-blocking log entries:

- TensorFlow emitted CPU/GPU capability warnings for missing CUDA libraries on a non-GPU host.
- The malformed fake mp3 smoke produced an expected ffmpeg error and HTTP `400`.

## Rollback

Rollback is expected to work by reverting Roadmap 3.11 production runtime changes, rebuilding only `genre-classifier`, restarting only `genre-classifier`, and verifying:

- `/health`
- `/classify` fixture
- malformed upload behavior
- logs

Rollback triggers:

- build failure
- startup failure
- `/health` failure
- `/classify` failure
- response shape drift
- provider default drift
- shadow unexpectedly enabled
- duplicate `Bitcast` registration in normal startup/classify path
- service crash after malformed upload
- unacceptable memory or latency behavior

## Result

Decision: `controlled_runtime_switch_validated`

No rollback trigger fired during Roadmap 3.11 validation.
