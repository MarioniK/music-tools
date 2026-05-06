# Roadmap 4.54: ONNX/MusiCNN pragmatic replacement criteria and preprocessing strategy reset

## Status

Documentation-only decision refinement.

`not_production_decision: true`
`strict_legacy_parity_required: false`
`output_drift_allowed: true`

Roadmap 4.54 does not approve a provider implementation, a default provider
switch, production migration, `/classify` contract changes, response shape
changes, dependency changes, runtime changes, or candidate selection outside
the official ONNX/MusiCNN lane.

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
- no production migration approval;
- no alternative candidate selection;
- no dependency changes;
- no model/audio file changes.

## Roadmap 4.53 clarification summary

Roadmap 4.53 reset the lightweight migration criteria after the ONNX
preprocessing blocker. The important clarification for Roadmap 4.54 is that
Lane B is not a generic pragmatic lightweight classifier search. Lane B is a
concrete ONNX/MusiCNN pragmatic replacement lane centered on the official
ONNX/MusiCNN candidate only.

The reset from Roadmap 4.53 remains in force:

- strict legacy parity is no longer mandatory for the lightweight migration
  path;
- output drift from `legacy_musicnn` is allowed if it is controlled,
  reproducible, and documented;
- the `/classify` contract remains immutable;
- the response shape remains immutable:
  - `ok`
  - `message`
  - `genres`
  - `genres_pretty`
- `legacy_musicnn` remains the default provider until separate approval is
  granted;
- this roadmap does not approve a production migration;
- this roadmap does not approve a provider switch.

## Candidate scope

Target candidate:

- `official_onnx_musicnn`

Candidate count:

- `1`

Alternative candidate selection is out of scope for Roadmap 4.54.

## Preprocessing clarification

The ONNX/MusiCNN path still technically requires preprocessing because the ONNX
input is `melspectrogram [187, 96]`.

However:

- preprocessing identical to `TensorflowPredictMusiCNN` is not required;
- documented and reproducible preprocessing is required;
- the preprocessing path must be describable, repeatable, and reviewable
  offline;
- local-only inference is preferred;
- no runtime network downloads are allowed.

This roadmap therefore resets the question from "match the legacy preprocessing
exactly" to "define a documented, reproducible preprocessing strategy that can
feed the official ONNX/MusiCNN input shape."

## Lane A

### `strict_onnx_musicnn_legacy_parity_replacement`

Status: `blocked` / `inactive`

Blockers:

- `LEGACY_INTERMEDIATE_NOT_EXPOSED`
- `MEL_INPUT_GENERATION_UNKNOWN`
- `PREPROCESSING_PARAMETERS_MISSING`
- `ESSENTIA_PREPROCESSING_CHAIN_UNCONFIRMED`
- `TENSOR_LAYOUT_UNKNOWN`
- `NORMALIZATION_UNKNOWN`

Lane A remains a strict parity/replacement attempt and is still blocked by the
same unknowns. Roadmap 4.54 does not attempt to solve these blockers.

## Lane B

### `pragmatic_onnx_musicnn_replacement`

Status: `active_for_preprocessing_strategy_design`

Target candidate:

- `official_onnx_musicnn`

Lane B is the only active lightweight lane in Roadmap 4.54. It is scoped to
preprocessing strategy design for the official ONNX/MusiCNN candidate and does
not imply approval of implementation, default switch, or production rollout.

## Lane B acceptance criteria

- `/classify` contract unchanged;
- response shape unchanged:
  - `ok`
  - `message`
  - `genres`
  - `genres_pretty`
- output drift from `legacy_musicnn` allowed;
- output stable and reproducible on approved legal fixtures;
- output mapped to controlled vocabulary;
- non-genre leakage controlled;
- preprocessing documented and reproducible;
- preprocessing identical to legacy not required;
- no runtime network downloads;
- local-only inference preferred;
- ONNX Runtime footprint meaningfully lighter than the TensorFlow /
  `essentia-tensorflow` production path;
- rollback simple;
- provider implementation separate gate;
- default provider switch separate gate;
- production migration separate gate.

## Explicit non-goals

Roadmap 4.54 does not include:

- alternative candidate selection;
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

Roadmap 4.55 — ONNX/MusiCNN pragmatic preprocessing strategy design.

Roadmap 4.55 goal:

- choose a documented and reproducible preprocessing path for
  `melspectrogram [187, 96]`;
- do not prove strict legacy parity;
- prepare an ONNX/MusiCNN prototype path.

