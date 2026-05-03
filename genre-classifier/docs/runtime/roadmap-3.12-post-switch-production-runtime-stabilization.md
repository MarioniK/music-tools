# Roadmap 3.12 - Post-switch production runtime stabilization

## Goal

Confirm and document post-switch stability of the `genre-classifier` production runtime after the Roadmap 3.11 switch.

## Scope

This validation covers only the production `genre-classifier` service from `/opt/music-tools/genre-classifier`.

Evidence was collected from the running production compose service on May 3, 2026 and stored under:

```text
docs/runtime/evidence/roadmap-3.12/
```

## Non-goals

- no provider switch
- no canary rollout
- no LLM cutover or LLM production adoption
- no migration to a lighter non-TensorFlow model
- no `/classify` contract change
- no response shape change
- no cache semantics change
- no runtime shadow enablement
- no broad runtime redesign
- no `tidal-parser` changes

## Roadmap 3.11 switch summary

Roadmap 3.11 completed the production runtime switch at commit `0b7066d4ba27a45271d13e793a4d8718be963bab`, tagged `v0.3.11`.

The production runtime moved from the legacy Python 3.6 / TensorFlow 1.15 stack to Python 3.12 with `essentia-tensorflow`. Application behavior remained unchanged:

- default provider remains `legacy_musicnn`
- `/classify` request contract is unchanged
- response shape is unchanged
- runtime shadow remains disabled by default
- `tidal-parser` is unchanged

## Post-switch runtime identity

Observed runtime identity:

- Python `3.12.13`
- TensorFlow `2.21.0`
- `essentia-tensorflow` `2.1b6.dev1389`
- Essentia `2.1-beta6-dev`
- numpy `2.4.4`
- protobuf `7.34.1`
- h5py `3.14.0`
- FastAPI `0.83.0`
- Pydantic `1.10.26`
- Uvicorn `0.16.0`
- Starlette `0.19.1`

The running compose service used image id:

```text
sha256:2ccb366bd05e691821d82e1348efdbc65bbcae35a1f2c171134449e5802fb55d
```

## Validation evidence

Validation results:

- `docker compose ps`: service `genre-classifier` was `Up` with port `8021` published.
- `/health`: HTTP `200`, body `{"ok":true}`.
- `/classify` fixture smoke: HTTP `200`.
- response shape remained exactly `ok`, `message`, `genres`, `genres_pretty`.
- provider default remained `legacy_musicnn`.
- runtime shadow remained disabled by default.
- Essentia-first model load passed.
- repeated classify smoke passed `10/10` HTTP `200`.
- malformed empty upload returned HTTP `400`.
- malformed fake mp3 upload returned HTTP `400`.
- unsupported text upload returned HTTP `400`.
- post-validation `docker compose ps` still showed the service `Up`.

Latency over the 10 repeated classify requests:

- min `9.509416s`
- max `10.992559s`
- avg `9.948980s`

## Observation evidence

Primary evidence files:

- `candidate-compose-ps.txt`
- `candidate-compose-ps-after-validation.txt`
- `candidate-runtime-identity.txt`
- `candidate-health.json`
- `candidate-health.meta.txt`
- `candidate/upload.classify.body.json`
- `candidate/upload.classify.meta.txt`
- `candidate-response-shape.txt`
- `candidate-provider-shadow-config.txt`
- `candidate-repeated-classify-latency-summary.txt`
- `candidate-malformed-uploads.txt`
- `candidate-docker-stats.txt`
- `candidate-logs-review.txt`
- `candidate-logs-tail-500.txt`
- `candidate-startup-logs-initial.txt`

The repeated classify request/response bodies are stored under:

```text
docs/runtime/evidence/roadmap-3.12/candidate/
```

## Logs review

Log review found:

- no duplicate `Bitcast` error in the running service logs
- no `RegisterAlreadyLocked` error in the running service logs
- no TensorFlow/Essentia import-order crash in the running service logs
- no unexpected model load crash
- expected TensorFlow CPU/GPU capability warnings on a non-GPU host
- ffmpeg errors only for malformed fake mp3 upload checks

The log tail includes two fake mp3 ffmpeg errors because the current container had prior validation traffic before the Roadmap 3.12 capture. Both are malformed-upload validation events and not startup or valid `/classify` failures.

## Memory/latency sanity

Post-validation `docker stats --no-stream` showed:

```text
376.6MiB / 4GiB
```

This is within the Roadmap 3.11 observed runtime range and did not indicate runaway memory growth during the smoke window.

Latency remained close to the Roadmap 3.11 validation baseline. The 10 repeated classify requests averaged `9.948980s`, with max `10.992559s`.

## Import-order invariant verification

Supported app-first / Essentia-first scenarios passed in isolated fresh processes:

- `essentia_first`: `exit_code=0`
- `essentia_standard_first`: `exit_code=0`
- `classify_import`: `exit_code=0`
- `app_main_import`: `exit_code=0`
- `classify_then_tensorflow`: `exit_code=0`
- `app_then_tensorflow`: `exit_code=0`
- `model_load_essentia_first`: `exit_code=0`
- `same_process_repeated_imports`: `exit_code=0`

The TensorFlow-first model-load path remains unsupported and documented only:

- `model_load_tensorflow_first`: `exit_code=1`
- observed failure: duplicate `Bitcast` op registration through `RegisterAlreadyLocked`

This matches the Roadmap 3.9 and Roadmap 3.11 accepted invariant: production must keep the app-first / Essentia-first path.

## Rollback window assessment

No rollback trigger fired during Roadmap 3.12 validation.

Rollback remains available by reverting the Roadmap 3.11 runtime packaging changes, rebuilding only `genre-classifier`, restarting only `genre-classifier`, and rechecking `/health`, `/classify`, malformed upload behavior, logs, memory, and latency.

Rollback should still be considered if production observation later shows:

- startup failure
- valid `/classify` failure
- response shape drift
- default provider drift
- runtime shadow unexpectedly enabled
- duplicate `Bitcast` / `RegisterAlreadyLocked` errors on supported production paths
- sustained memory growth beyond host budget
- unacceptable latency regression under normal traffic

## Remaining risks

- TensorFlow-first mixed import order remains a known unsupported path.
- Validation was a smoke/stability window, not a canary rollout or long-duration load test.
- TensorFlow emits expected non-GPU CUDA warnings; these are noisy but non-blocking.
- Current runtime still carries TensorFlow/Essentia startup and inference cost.

## Decision

Decision: `production_runtime_stabilized`

Roadmap 3.12 confirms the Roadmap 3.11 production runtime baseline is stable for the validated post-switch smoke scope.

## Recommendation for next roadmap

Proceed to the next roadmap without changing the provider default or `/classify` contract.

Recommended next work:

- continue normal production observation for the Python 3.12 + `essentia-tensorflow` baseline
- keep the import-order invariant documented as an operational guardrail
- defer any provider/canary/LLM or lighter-model work to a separate roadmap with its own rollout plan
