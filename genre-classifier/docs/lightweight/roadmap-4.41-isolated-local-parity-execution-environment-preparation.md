# Roadmap 4.41 - Isolated local parity execution environment preparation

## Purpose

Roadmap 4.41 prepares an isolated local execution environment for a future real MusiCNN TensorFlow vs ONNX Runtime parity run. It is environment preparation only.

This step does not migrate production runtime, does not implement an ONNX provider, does not switch defaults, and does not approve inference beyond a future local spike.

## Scope

Only `genre-classifier` is in scope. `tidal-parser` is untouched.

The production invariants remain unchanged:

- default provider remains `legacy_musicnn`;
- production classifier path remains legacy MusiCNN;
- `/classify` contract is unchanged;
- response shape remains `ok`, `message`, `genres`, `genres_pretty`;
- runtime shadow remains disabled by default;
- cache semantics are unchanged.

## Local-only Inputs

Roadmap 4.41 checks the existing local-only model artifact workspace using sanitized public labels. Model binaries remain outside the repository and are not committed.

Expected local-only artifacts:

- `msd-musicnn-1.onnx`
- `msd-musicnn-1.pb`
- `msd-musicnn-1.json`

Audio fixtures must remain outside the repository in the local fixture workspace. If no fixtures are present, Roadmap 4.41 records `FIXTURE_FILES_MISSING` and does not create fake audio files.

## Isolated Environment Policy

The isolated local environment is represented in public reports as `isolated_venv`.

`onnxruntime` may be installed only into that isolated local environment. Production dependency files, Dockerfiles, Docker Compose files, provider factory wiring, and runtime code are not changed.

TensorFlow, Essentia, and `essentia.standard` are checked for local availability only. If unavailable, the report records blockers instead of mutating production files.

## Public Report

The sanitized report is:

```text
docs/lightweight/evaluation/parity-scaffold/musicnn-onnx-parity-environment-preparation-report.json
```

The report is safe for commit:

- no audio binaries;
- no model binaries;
- no venv files;
- no private full local paths;
- no production approval claims;
- no simulated parity metrics.

## Result

The local model artifacts are available. The fixture workspace exists, but contains no audio fixtures, so fixture count is `0`.

The isolated local environment is present and `onnxruntime` is available there. TensorFlow and Essentia are unavailable in the local baseline environment, so baseline runtime remains unavailable.

`environment_status`: `partially_ready`

Remaining blockers:

- `FIXTURE_FILES_MISSING`
- `TENSORFLOW_UNAVAILABLE`
- `ESSENTIA_UNAVAILABLE`
- `BASELINE_RUNTIME_UNAVAILABLE`
- `PARITY_RUN_NOT_EXECUTED`

## Next Step

Add real local-only audio fixtures with clear provenance, then make TensorFlow/Essentia baseline runtime available in an isolated local environment before executing numeric parity.

