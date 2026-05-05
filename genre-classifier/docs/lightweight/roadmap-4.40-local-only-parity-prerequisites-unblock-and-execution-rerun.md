# Roadmap 4.40 - Local-only parity prerequisites unblock and execution rerun

## Purpose

Roadmap 4.40 is a practical unblock/rerun step for the local-only MusiCNN TensorFlow vs ONNX Runtime parity path. It is not planning-only, not a production migration, not a provider implementation, and not a default provider switch.

The goal is to re-check the prerequisites that blocked Roadmap 4.39 and, only if they are already available in the local/dev environment, execute numeric local-only parity evidence.

## Inherited Roadmap 4.39 Blockers

Roadmap 4.39 recorded these blockers:

- `FIXTURE_DIR_MISSING`
- `ONNXRUNTIME_UNAVAILABLE`
- `BASELINE_RUNTIME_UNAVAILABLE`
- `PARITY_RUN_NOT_EXECUTED`

## Local/dev Runtime Policy

`onnxruntime`, `tensorflow`, `essentia`, and `essentia.standard` may be used only if they are already importable in the local/dev environment. Roadmap 4.40 does not add runtime dependencies, does not edit requirements files, does not edit Dockerfiles, and does not change Docker Compose.

`onnxruntime` is not approved as a production dependency by this step.

## Fixture Outside-repo Policy

Audio fixtures must remain local-only and outside the repository. The allowed fixture location is `/tmp/music-tools-onnx-parity/fixtures/`.

No audio files are added under the repo root, `docs/`, `tests/`, `app/`, or any path under `/opt/music-tools/genre-classifier`.

## Sanitized Report Policy

The public report is:

```text
docs/lightweight/evaluation/parity-scaffold/musicnn-onnx-parity-spike-report.json
```

It records sanitized prerequisite status, blocker codes, and metrics only when produced by real local execution. It must not contain audio binaries, model binaries, private fixture paths, production approval claims, or simulated metrics.

## Baseline Policy

`legacy_musicnn` remains the production baseline. The default provider remains unchanged, the provider factory remains unchanged, and the `/classify` response shape remains unchanged:

- `ok`
- `message`
- `genres`
- `genres_pretty`

## Result

The local model artifacts were present under the local-only artifact area:

- `msd-musicnn-1.onnx`
- `msd-musicnn-1.pb`
- `msd-musicnn-1.json`

The local fixture directory was missing, and the local Python environment did not provide `onnxruntime`, `tensorflow`, `essentia`, or `essentia.standard`.

Numeric parity execution was not possible. No TensorFlow/Essentia baseline capture was executed. No ONNX Runtime capture was executed. Metrics remain `null`, and the report records exact blockers instead of simulated values.

`decision_status`: `blocked_missing_runtime`

Remaining blockers:

- `FIXTURE_DIR_MISSING`
- `ONNXRUNTIME_UNAVAILABLE`
- `BASELINE_RUNTIME_UNAVAILABLE`
- `PARITY_RUN_NOT_EXECUTED`

## Explicit Non-goals

- No production provider implementation.
- No provider factory changes.
- No default provider switch.
- No Docker/runtime migration.
- No production dependency changes.
- No `onnxruntime` in requirements.
- No `/classify` calls.
- No response shape changes.
- No cache changes.
- No `tidal-parser` changes.
- No release/tag.
