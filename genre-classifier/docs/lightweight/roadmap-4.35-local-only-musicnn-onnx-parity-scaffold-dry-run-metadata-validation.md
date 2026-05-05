# Roadmap 4.35 - Local-only MusiCNN ONNX parity scaffold dry-run metadata-validation

## Status

Implemented as a local-only, CLI-only dry-run scaffold.

This is a metadata-validation safe-slice only. It is non-production-facing and
does not execute model inference.

## Scope

Roadmap 4.35 adds:

- `scripts/lightweight/musicnn_onnx_parity_scaffold.py`;
- targeted tests in `tests/lightweight/test_musicnn_onnx_parity_scaffold.py`;
- this documentation artifact.

The scaffold validates recorded metadata semantics from the existing evidence
report:

```text
docs/lightweight/evaluation/model-provenance/local-musicnn-onnx-artifact-metadata-evidence-report.json
```

It also checks the documented Roadmap 4.32 JSON metadata equivalence decision.

## Why dry-run after Roadmap 4.34

Roadmap 4.34 approved only future creation of scaffold code in dry-run /
metadata-validation mode.

Approval to create scaffold code was not approval to run TensorFlow inference,
run ONNX inference, compare raw model outputs, add `onnxruntime`, implement a
provider, switch the default provider, or migrate production.

Roadmap 4.35 therefore starts with a stdlib-only metadata validator. It records
whether the local-only evidence is internally coherent before any later
approval gate considers inference.

## CLI behavior

Supported commands from `/opt/music-tools/genre-classifier`:

```text
python3 scripts/lightweight/musicnn_onnx_parity_scaffold.py
python3 scripts/lightweight/musicnn_onnx_parity_scaffold.py --mode dry-run
python3 scripts/lightweight/musicnn_onnx_parity_scaffold.py --evidence-report docs/lightweight/evaluation/model-provenance/local-musicnn-onnx-artifact-metadata-evidence-report.json
```

The command without arguments safely runs the default dry-run.

The CLI writes structured JSON to stdout and returns non-zero for expected
validation failures. Expected failures are reported as JSON without traceback.

## Checks performed

The scaffold validates recorded metadata only:

- the evidence report exists and is readable JSON;
- required artifact roles are present;
- required artifact records have positive integer `file_size_bytes`;
- required artifact records have lowercase 64-character SHA256 strings;
- known Roadmap 4.30 size and SHA256 values are recorded;
- official/local PB matches the current bundled PB by SHA256 and records that
  observation;
- the JSON difference is recorded as a review item, not parity evidence;
- the Roadmap 4.32 parsed-JSON equivalence decision is documented;
- official/local artifact paths are recorded under
  `/tmp/music-tools-onnx-parity/`;
- official/local artifacts are recorded as `artifact_in_repo: false` and
  `committed_to_repo: false`;
- unexpected approval flags fail validation if set true.

The default dry-run does not require physical existence of artifacts under
`/tmp/music-tools-onnx-parity/`. It validates only the recorded paths and
metadata. It does not open ONNX, PB, JSON model artifact files, read audio
fixtures, or download anything.

## Safety boundaries

Roadmap 4.35 does not approve inference.

Roadmap 4.35 does not approve `onnxruntime`.

Roadmap 4.35 does not approve provider implementation.

Roadmap 4.35 does not approve default provider switch.

Roadmap 4.35 does not approve production migration.

The scaffold does not:

- import TensorFlow;
- import `onnxruntime`;
- import Essentia;
- import production app code;
- import providers;
- call `/classify`;
- execute models;
- compare raw model outputs;
- add dependencies;
- add model files;
- add audio fixtures;
- add network or download logic;
- change Dockerfile or Docker Compose;
- change controlled vocabulary;
- change the `/classify` contract or response shape;
- touch `tidal-parser`.

`legacy_musicnn` remains the production baseline. The default provider remains
`legacy_musicnn`.

The `/classify` response shape remains unchanged:

- `ok`;
- `message`;
- `genres`;
- `genres_pretty`.

## Validation and test results

Initial validation commands completed from `/opt/music-tools/genre-classifier`:

```text
python3 scripts/lightweight/musicnn_onnx_parity_scaffold.py
python3 scripts/lightweight/musicnn_onnx_parity_scaffold.py --mode dry-run
python3 scripts/lightweight/validate_evaluation_artifacts.py
python3 -m pytest tests/lightweight -q
```

The scaffold dry-run returned `ok: true`, `mode: dry-run`, and all runtime
touch/import/inference flags as `false`.

The targeted scaffold tests cover:

- default dry-run success;
- explicit `--mode dry-run` success;
- explicit evidence report path success;
- runtime/import/touch flags remain false;
- invalid report path failure without traceback;
- missing required role failure;
- unexpected inference approval failure;
- unexpected production approval failure;
- hash mismatch failure;
- output does not claim final model parity or production approval.

## Non-goals

Roadmap 4.35 does not:

- prove numeric model equivalence;
- prove raw output equivalence;
- prove preprocessing equivalence;
- prove final genre equivalence;
- approve TensorFlow baseline execution;
- approve ONNX Runtime execution;
- approve a provider implementation;
- approve production readiness;
- change production runtime behavior.

## Decision

The dry-run metadata-validation scaffold is implemented and remains local-only.

Recorded metadata validation may pass, but that is not numeric/model/final
genre parity proof.

## Next step recommendation

Review dry-run metadata-validation output before any inference approval.
