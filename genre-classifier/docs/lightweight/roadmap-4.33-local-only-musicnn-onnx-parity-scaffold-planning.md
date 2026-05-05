# Roadmap 4.33 — Local-only MusiCNN ONNX parity scaffold planning

## Status

Completed documentation/planning safe-slice.

## Scope

Roadmap 4.33 is limited to documentation and planning only.

This slice is:

- documentation/planning only;
- non-production-facing;
- local-only parity scaffold planning only.

This slice does not include or approve:

- classifier implementation;
- actual parity runner;
- model integration;
- model files in repo;
- production dependency changes;
- `onnxruntime` addition;
- provider implementation;
- provider factory changes;
- default-provider switch;
- shadow execution;
- canary;
- production migration;
- runtime changes;
- Dockerfile / Docker Compose changes;
- `/classify` contract changes;
- response shape changes;
- `tidal-parser` changes.

## Current evidence state after Roadmap 4.32

The official/local PB matches the current bundled PB by SHA256:

```text
cdea0722bcee7f731286843f2233e3aa69887bb5c3e2dce011eff55f38d04f3e
```

The official/local JSON mismatch from Roadmap 4.30 and Roadmap 4.31 has been
reviewed.

The JSON mismatch is final-newline-only.

Parsed JSON metadata is equivalent.

Labels/order are equal.

A real local-only artifact metadata evidence report exists and is validated.

Inference is not approved.

`onnxruntime` is not approved.

Provider implementation is not approved.

Production migration is not approved.

`legacy_musicnn` remains the only production classifier path.

## Why this step is needed

PB identity and JSON equivalence are positive evidence for considering an ONNX
parity path, but they do not prove numeric parity, model-output parity, or
final response parity.

Before any local-only inference or comparison work is created, the project
needs a narrow scaffold plan that defines inputs, boundaries, comparison
dimensions, report shape, approval gates, success criteria, and no-go criteria.

ONNX is being evaluated as a potential runtime replacement for the current
legacy MusiCNN path, not as a new semantic classifier lane. The baseline remains
the existing `legacy_musicnn` behavior.

## Future scaffold purpose

A future scaffold, only after separate approval, should:

- compare the current TensorFlow PB path against the official/local ONNX path;
- preserve current `legacy_musicnn` semantics;
- prove or reject parity before any runtime replacement work;
- avoid production API and provider wiring.

## Future inputs

Current bundled production baseline:

- `app/models/msd-musicnn-1.pb`;
- `app/models/msd-musicnn-1.json`.

Official/local artifacts outside repo:

- `/tmp/music-tools-onnx-parity/msd-musicnn-1.onnx`;
- `/tmp/music-tools-onnx-parity/msd-musicnn-1.json`;
- `/tmp/music-tools-onnx-parity/msd-musicnn-1.pb` optional/reference.

Future optional inputs only after separate approval:

- local legal audio fixture manifest;
- TensorFlow baseline output captures;
- ONNX output captures.

## Future scaffold responsibilities

A future scaffold should:

- load/record artifact metadata;
- validate artifact identity before comparison;
- validate JSON labels/order equivalence;
- define fixture manifest input;
- define baseline output capture strategy;
- define ONNX output capture strategy;
- define raw output comparison metrics;
- define semantic output comparison metrics;
- define report format;
- define no-go criteria;
- avoid production API and provider wiring.

## Future comparison dimensions

Future comparison should cover:

- artifact identity;
- metadata identity;
- preprocessing input compatibility;
- raw output shape;
- raw output numeric delta:
  - `max_abs_diff`;
  - `mean_abs_diff`;
  - tolerance;
- top-N overlap;
- final genres overlap;
- `genres_pretty` match;
- empty output behavior;
- warning/failure behavior;
- latency/memory metrics only if inference later approved.

## Future execution boundaries

Future execution, if separately approved, must remain:

- local-only;
- no production traffic;
- no `/classify` calls;
- no provider factory changes;
- no default provider switch;
- no Docker/runtime changes;
- no model files in repo;
- no audio fixtures in repo;
- no network/download logic;
- no production migration.

## Future approval gates

Future work requires separate approval for each gate:

- approval to create parity scaffold code;
- approval to add optional local-only `onnxruntime` dev dependency or local env
  instruction;
- approval to run TensorFlow baseline inference;
- approval to run ONNX inference;
- approval to compare outputs;
- approval to review parity evidence;
- approval to consider provider implementation;
- approval to consider production migration.

## Future evidence report format

A future evidence report should use this structure:

```text
# Local-only MusiCNN ONNX parity evidence report

## Summary

## Artifact metadata

## Fixture manifest

## Baseline outputs

## ONNX outputs

## Raw comparison metrics

## Semantic comparison metrics

## Warnings

## No-go items

## Decision

- continue
- revise
- block
- reject
```

## Success criteria

Future parity work may continue only if:

- artifact identity is accepted;
- JSON metadata equivalence is accepted;
- preprocessing compatibility is established;
- raw output shape is compatible;
- numeric deltas are within agreed tolerance;
- top-N/final genres parity is acceptable;
- `genres_pretty` behavior is acceptable;
- no response shape changes are required;
- no `/classify` contract changes are required;
- no provider/default switch is required for evaluation;
- no model files are added to the repo;
- rollback remains simple.

## No-go criteria

Future parity work must stop or return for review if any of these are true:

- preprocessing is incompatible;
- ONNX input/output is not comparable;
- raw output shape mismatches;
- numeric drift is too large;
- top-N/final genres drift is unacceptable;
- `genres_pretty` parity breaks;
- `/classify` contract change is required;
- provider/default switch is required to evaluate;
- model files are required in repo;
- runtime network downloads are required;
- production Docker/runtime changes are required before proof;
- license/provenance blocker exists.

## Decision options

Available decisions after this planning slice:

- continue to local-only parity scaffold implementation approval gate;
- continue to fixture/manifest preparation planning;
- continue to preprocessing compatibility review;
- block until local legal audio fixtures are approved;
- block until ONNX runtime local-only execution policy is approved;
- keep `legacy_musicnn` as only production path.

## Recommended decision

Recommended decision for Roadmap 4.33:

- do not implement scaffold in Roadmap 4.33;
- do not add `onnxruntime`;
- do not run inference;
- prepare planning only;
- next step may be approval gate for creating a local-only parity scaffold;
- keep `legacy_musicnn` as production baseline.

## Explicit non-goals

Roadmap 4.33 does not include or approve:

- production classifier code;
- production provider implementation;
- provider factory changes;
- `onnxruntime` or dependency changes;
- model files;
- audio fixtures;
- network/download logic;
- inference;
- TensorFlow/ONNX model execution;
- `/classify` calls;
- controlled vocabulary changes;
- runtime changes;
- Dockerfile/Docker Compose changes;
- default provider change;
- `/classify` contract change;
- response shape change;
- cache semantics change;
- `tidal-parser` changes;
- shadow execution;
- canary rollout;
- LLM cutover;
- production migration;
- tag/release.
