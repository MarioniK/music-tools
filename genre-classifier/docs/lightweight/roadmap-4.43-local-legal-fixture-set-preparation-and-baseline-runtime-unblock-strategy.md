# Roadmap 4.43 - Local legal fixture set preparation and baseline runtime unblock strategy

## Goal

Roadmap 4.43 prepares a safe path toward a future local-only MusiCNN TensorFlow vs ONNX Runtime numeric parity run. It checks the two remaining blocker areas without running parity, model inference, or production provider code:

- legal local audio fixtures outside the repository;
- a baseline runtime strategy for the current `legacy_musicnn` path.

This is an unblock strategy, not a production migration. It does not approve provider implementation, a default provider switch, or runtime changes.

## Fixture Inspection Result

The allowed local fixture workspace exists, but it contains no audio fixture files.

`fixture_status`: `missing`

`fixture_count`: `0`

Because fixtures are absent, no fake audio was created, no audio was downloaded, and no invented fixture metadata was recorded. The blocker is `FIXTURE_FILES_MISSING`.

## Sanitized Fixture Policy

Audio fixtures must stay outside the repository and outside any git-tracked path. They must not be copied into the repository root, `docs/`, `tests/`, `app/`, or any path under `genre-classifier`.

When fixtures exist, committed reports may include only sanitized metadata: `fixture_id`, `file_size_bytes`, `sha256`, extension or audio format, optional `duration_seconds` when safely available, source type, usage permission, license status, provenance notes, and explicitly available category or tags.

Committed reports must not include audio bytes, model binaries, venv contents, private full local paths, or unverified provenance claims.

## Baseline Runtime Checks

The local service environment was checked with import-only commands:

```text
python3 -c "import tensorflow as tf; print(tf.__version__)"
python3 -c "import essentia, essentia.standard; print('essentia ok')"
```

TensorFlow is not importable locally. Essentia and `essentia.standard` are not importable locally. The production provider was not imported, `/classify` was not called, and no TensorFlow model execution occurred.

## Selected Baseline Runtime Strategy

`baseline_runtime_strategy`: `existing_container_local_only`

`baseline_runtime_status`: `container_strategy_candidate`

The local service environment is unavailable for baseline capture, but the service has a `genre-classifier`-scoped Dockerfile, Compose file, and production requirements that include TensorFlow and Essentia. A future baseline capture may use the existing local service container path only after a separate approval step.

Any future command must be run from the `genre-classifier` service directory and must avoid monorepo-root Docker Compose, rebuilds, `/classify` calls, model output comparison, and numeric parity unless those actions are explicitly approved for that step.

`isolated_baseline_env` was not selected because there is no explicit safe local TensorFlow plus Essentia baseline environment for this step.

## ONNX Runtime Isolated Env Status

The isolated ONNX Runtime check succeeded in the local parity venv and reported version `1.25.1`.

This does not add `onnxruntime` to production requirements and does not approve production runtime use.

## Decision

`decision_status`: `baseline_container_strategy_selected`

Remaining blockers:

- `FIXTURE_FILES_MISSING`
- `TENSORFLOW_UNAVAILABLE`
- `ESSENTIA_UNAVAILABLE`
- `BASELINE_CONTAINER_STRATEGY_SELECTED`
- `BASELINE_ENVIRONMENT_NOT_REPRODUCIBLE`
- `NUMERIC_PARITY_NOT_APPROVED`

## Next Step Recommendation

Add legal local-only audio fixtures with publishable sanitized metadata, then separately approve a scoped `genre-classifier` container baseline capture before any numeric parity run.

## Explicit Non-Goals

- No numeric parity.
- No TensorFlow model execution.
- No ONNX model execution.
- No model output comparison.
- No `/classify` calls.
- No provider factory changes.
- No default provider changes.
- No `/classify` contract changes.
- No response shape changes.
- No cache behavior changes.
- No production dependency changes.
- No Dockerfile or Compose changes.
- No audio binaries in the repository.
- No model binaries in the repository.
- No venv committed.
- No `tidal-parser` changes.
- No commit, push, tag, or release.
