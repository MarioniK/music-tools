# Roadmap 4.39 - Local-only MusiCNN TensorFlow vs ONNX Runtime parity spike

## Purpose

Roadmap 4.39 checks whether the current legacy MusiCNN baseline can be compared locally against a local-only ONNX Runtime execution path.

This is a controlled evidence-producing spike. It is not a production migration, not a provider implementation, not a dependency approval, and not a default provider switch.

## Local prerequisites checked

The spike checked for local-only model artifacts under `/tmp/music-tools-onnx-parity/`:

- `msd-musicnn-1.onnx`
- `msd-musicnn-1.pb`
- `msd-musicnn-1.json`

It also checked for local-only audio fixtures under `/tmp/music-tools-onnx-parity/fixtures/` and for local runtime availability without installing dependencies:

- `onnxruntime`
- `tensorflow`
- `essentia`
- `essentia.standard`

## Result

The local-only model artifacts were present, but the local fixture directory was missing and the local Python environment did not provide `onnxruntime`, `tensorflow`, `essentia`, or `essentia.standard`.

No TensorFlow/Essentia baseline capture was executed. No ONNX Runtime capture was executed. No `/classify` request was made.

## Decision Status

`decision_status`: `blocked`

The parity run was not executed because local-only prerequisites are missing. The committed evidence report records blocker codes instead of fake metrics.

## Blockers

- `FIXTURE_DIR_MISSING`: `/tmp/music-tools-onnx-parity/fixtures/` is missing.
- `ONNXRUNTIME_UNAVAILABLE`: `onnxruntime` is not importable in the local environment.
- `BASELINE_RUNTIME_UNAVAILABLE`: TensorFlow/Essentia baseline modules are not importable.
- `PARITY_RUN_NOT_EXECUTED`: numeric parity comparison was not run.

## Evidence Report

The sanitized report is:

```text
docs/lightweight/evaluation/parity-scaffold/musicnn-onnx-parity-spike-report.json
```

Because the run is blocked, parity metrics are `null` and `preprocessing_alignment_status` is `not_evaluated`.

## Explicit Non-goals

- No production migration.
- No provider implementation.
- No default provider switch.
- No production runtime or dependency change.
- No Dockerfile or Docker Compose change.
- No `/classify` call.
- No response shape change.
- No cache semantics change.
- No audio or model files added to the repository.
- No `tidal-parser` change.
- No commit, tag, push, release, or production approval.

## Safety Confirmations

- `legacy_musicnn` remains the production baseline.
- The default provider is unchanged.
- The `/classify` contract is unchanged.
- The response shape is unchanged.
- Docker and Docker Compose are unchanged.
- Production dependencies are unchanged.
- Provider factory and default provider wiring are unchanged.
- No audio files were committed.
- No model files were committed.
- `tidal-parser` was not touched.
