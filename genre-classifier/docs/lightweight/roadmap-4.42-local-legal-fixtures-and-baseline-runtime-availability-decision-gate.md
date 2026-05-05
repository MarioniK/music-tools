# Roadmap 4.42 - Local legal fixtures and baseline runtime availability decision gate

## Purpose

Roadmap 4.42 is a two-blocker decision gate for future local-only MusiCNN TensorFlow vs ONNX Runtime numeric parity. It is not a production migration, not a provider implementation, and not a default provider switch.

The gate checks only whether the two practical prerequisites for a later numeric parity run are actually available:

- legal local audio fixtures outside the repository;
- importable TensorFlow and Essentia baseline runtime in the local baseline environment.

## Why numeric parity remains blocked

Numeric parity is not meaningful without real, legally usable audio fixtures. It is also not reproducible unless the legacy MusiCNN baseline runtime can be imported without changing production dependencies or runtime wiring.

If either blocker is present, Roadmap 4.42 records explicit blocker codes and keeps `approved_for_numeric_parity_run: false`.

## Fixture metadata sanitation policy

Allowed fixture location:

```text
/tmp/music-tools-onnx-parity/fixtures/
```

Audio fixtures must remain outside the repository. They must not be copied into `docs/`, `tests/`, `app/`, the repository root, or any git-tracked path.

If fixtures are present, the committed report may include only sanitized metadata:

- `fixture_id`;
- file extension or format;
- `file_size_bytes`;
- `sha256`;
- `duration_seconds`, only when available through a safe lightweight check;
- optional category, only when safely inferable from a filename or explicit local manifest.

The report must not include full local paths, private names, raw audio, fake audio, or fake fixture metadata.

## Import-only baseline runtime checks

Roadmap 4.42 uses import checks only:

```text
python3 -c "import tensorflow as tf; print(tf.__version__)"
python3 -c "import essentia, essentia.standard; print('essentia ok')"
```

It does not install TensorFlow or Essentia, mutate production dependency files, import the baseline provider, run model inference, or call `/classify`.

## ONNX Runtime isolated env check

The isolated ONNX Runtime environment is checked separately:

```text
/tmp/music-tools-onnx-parity/venv/bin/python -c "import onnxruntime; print(onnxruntime.__version__)"
```

This check does not add `onnxruntime` to production requirements and does not approve production runtime use.

## Blocker behavior

Roadmap 4.42 records `FIXTURE_FILES_MISSING` when no legal local audio fixtures are available. It records `TENSORFLOW_UNAVAILABLE`, `ESSENTIA_UNAVAILABLE`, and `BASELINE_RUNTIME_UNAVAILABLE` when the baseline imports fail.

If fixture provenance is unclear, the decision status must be `blocked_fixture_provenance_unclear`. If the isolated ONNX Runtime environment is missing, the report records `ONNXRUNTIME_ENV_NOT_AVAILABLE`.

## Result

The local fixture workspace exists but contains no audio fixtures.

TensorFlow and Essentia are unavailable in the local baseline environment. The isolated ONNX Runtime environment is available and reports version `1.25.1`.

`decision_status`: `blocked_missing_fixtures_and_baseline_runtime`

Remaining blockers:

- `FIXTURE_FILES_MISSING`
- `TENSORFLOW_UNAVAILABLE`
- `ESSENTIA_UNAVAILABLE`
- `BASELINE_RUNTIME_UNAVAILABLE`
- `NUMERIC_PARITY_NOT_APPROVED`

## Next step recommendation

Add legal local-only audio fixtures with publishable sanitized metadata and provide a reproducible local TensorFlow/Essentia baseline runtime, then re-run this decision gate before numeric parity.

If the baseline runtime is available only through an existing local container path in a future step, document a local-only container command scoped to `genre-classifier` before running it. Do not use the monorepo-root Docker Compose path for this parity gate.

## Explicit non-goals

- No audio files in the repository.
- No model files in the repository.
- No fake audio.
- No fake fixture metadata.
- No TensorFlow or Essentia installation.
- No production dependency changes.
- No Dockerfile or Docker Compose changes.
- No provider factory changes.
- No default provider switch.
- No `/classify` calls.
- No cache behavior changes.
- No TensorFlow or ONNX model inference.
- No numeric parity run.
- No `tidal-parser` changes.
- No commit, tag, or push.

## Safety confirmations

- `legacy_musicnn` remains the baseline.
- Production runtime remains unchanged.
- Production dependencies remain unchanged.
- Docker files remain unchanged.
- Provider/default wiring remains unchanged.
- The `/classify` contract and response shape remain unchanged.
- No audio, model, or venv files are committed.
