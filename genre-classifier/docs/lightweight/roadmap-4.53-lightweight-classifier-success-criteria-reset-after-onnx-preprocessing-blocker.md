# Roadmap 4.53: Lightweight classifier success criteria reset after ONNX preprocessing blocker

## Status

Documentation-only decision reset.

`not_production_decision: true`
`strict_parity_required: false`
`output_drift_allowed: true`

Roadmap 4.53 does not approve a provider implementation, a default provider
switch, production migration, `/classify` contract changes, response shape
changes, dependency changes, or runtime changes.

## AGENTS.md compliance

This artifact was prepared after reading and following
`/opt/music-tools/AGENTS.md`.

Confirmed constraints followed here:

- work limited to `genre-classifier`;
- `tidal-parser` untouched;
- no Docker Compose run;
- no Docker rebuild;
- no `/classify` calls;
- no inference;
- no production code changes;
- no provider switch approval;
- no production migration approval.

## Roadmap 4.52 blocker summary

Roadmap 4.52 concluded with:

- `alignment_status: blocked`;
- `blockers`:
  - `LEGACY_INTERMEDIATE_NOT_EXPOSED`
  - `MEL_INPUT_GENERATION_UNKNOWN`
  - `PREPROCESSING_PARAMETERS_MISSING`
  - `ESSENTIA_PREPROCESSING_CHAIN_UNCONFIRMED`
  - `TENSOR_LAYOUT_UNKNOWN`
  - `NORMALIZATION_UNKNOWN`

Roadmap 4.52 also recorded that:

- ONNX Runtime is available;
- ONNX model metadata is available;
- ONNX fixture output capture remains not approved;
- the required `melspectrogram [187, 96]` preprocessing path is not
  demonstrably aligned with the current legacy `TensorflowPredictMusiCNN`
  production path.

## Previous objective

The previous Roadmap 4 objective was:

- strict legacy parity;
- strict ONNX `MusiCNN` runtime replacement.

That objective is now too strict for the current lightweight migration phase.

## Updated objective

The updated Roadmap 4 objective is:

- pragmatic lightweight classifier replacement;
- lighter local classifier/runtime evaluation for future candidate selection;
- preserve the existing `/classify` contract and response shape.

## Decision reset

Roadmap 4.53 resets the success criteria as follows:

- strict parity is no longer mandatory for Roadmap 4 lightweight migration;
- output drift from `legacy_musicnn` is allowed if it is controlled,
  reproducible, and documented;
- `/classify` contract remains immutable;
- response shape remains immutable:
  - `ok`
  - `message`
  - `genres`
  - `genres_pretty`
- `legacy_musicnn` remains the default provider until separate approval is
  granted;
- this roadmap does not approve a production migration;
- this roadmap does not approve a provider switch.

## Lane split

### Lane A: `strict_onnx_musicnn_runtime_replacement`

Status: `blocked`

Blockers:

- `LEGACY_INTERMEDIATE_NOT_EXPOSED`
- `MEL_INPUT_GENERATION_UNKNOWN`
- `PREPROCESSING_PARAMETERS_MISSING`
- `ESSENTIA_PREPROCESSING_CHAIN_UNCONFIRMED`
- `TENSOR_LAYOUT_UNKNOWN`
- `NORMALIZATION_UNKNOWN`

### Lane B: `pragmatic_lightweight_classifier_replacement`

Status: `open_for_candidate_selection`

Purpose:

- lighter local classifier/runtime with the same `/classify` contract and
  response shape.

## Lane B acceptance criteria

- `/classify` contract unchanged;
- response shape unchanged:
  - `ok`
  - `message`
  - `genres`
  - `genres_pretty`
- `legacy_musicnn` remains the default provider until separate switch approval;
- output does not need to match the legacy baseline exactly;
- output must be stable and reproducible on approved legal fixtures;
- output must be mapped to controlled vocabulary;
- descriptor and non-genre leakage must be controlled;
- empty and error behavior must be documented;
- model/runtime footprint must be meaningfully lighter than the current
  TensorFlow / `essentia-tensorflow` path;
- local-only inference is preferred;
- no runtime network downloads;
- rollback must be simple;
- provider implementation requires a separate approval gate;
- default provider switch requires a separate approval gate.

## Explicit non-goals

Roadmap 4.53 does not include:

- production code changes;
- provider implementation;
- provider factory changes;
- default provider switch;
- dependency changes;
- Dockerfile changes;
- Compose file changes;
- Docker Compose run;
- Docker rebuild;
- `/classify` calls;
- inference;
- ONNX output capture;
- TensorFlow baseline rerun;
- TensorFlow vs ONNX comparison;
- final parity claim;
- production readiness claim;
- `tidal-parser` changes;
- audio/model binaries;
- commit/tag/push.

## Next recommendation

Roadmap 4.54: Pragmatic lightweight classifier candidate selection and
evaluation criteria.

