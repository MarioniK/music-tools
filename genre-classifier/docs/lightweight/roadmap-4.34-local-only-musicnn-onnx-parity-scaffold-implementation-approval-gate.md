# Roadmap 4.34 - Local-only MusiCNN ONNX parity scaffold implementation approval gate

## Status

Documentation-only approval gate.

This slice records the recommended approval decision before any future
local-only MusiCNN ONNX parity scaffold implementation.

No scaffold code is created in Roadmap 4.34.

## Scope

Roadmap 4.34 is:

- documentation-only;
- approval-gate only;
- safe-slice;
- non-production-facing;
- local-only parity scaffold implementation approval review only.

Roadmap 4.34 does not include:

- scaffold implementation;
- actual parity runner;
- inference;
- ONNX Runtime execution;
- TensorFlow inference execution;
- `/classify` calls;
- model integration;
- provider implementation;
- provider factory changes;
- production dependency changes;
- runtime changes;
- Dockerfile or Docker Compose changes;
- `tidal-parser` changes;
- tag, release, commit, or push.

## Current state after Roadmap 4.33

Roadmap 4.30 prepared real local-only MusiCNN ONNX/PB/JSON artifacts outside
the repository.

Real local-only artifacts are under:

- `/tmp/music-tools-onnx-parity/msd-musicnn-1.onnx`;
- `/tmp/music-tools-onnx-parity/msd-musicnn-1.json`;
- `/tmp/music-tools-onnx-parity/msd-musicnn-1.pb`.

Current bundled production baseline artifacts are:

- `app/models/msd-musicnn-1.pb`;
- `app/models/msd-musicnn-1.json`.

PB identity is positive. The official/local PB matches the current bundled PB
by SHA256:

```text
cdea0722bcee7f731286843f2233e3aa69887bb5c3e2dce011eff55f38d04f3e
```

Roadmap 4.31 added validation coverage for the real local-only artifact
evidence report.

Roadmap 4.32 accepted JSON metadata equivalence:

- `raw_equal: false`;
- `parsed_json_equal: true`;
- `labels set equal: true`;
- `label order equal: true`;
- `classification: harmless_formatting_only`.

Roadmap 4.33 created parity scaffold planning.

No inference has been approved.

ONNX Runtime has not been approved.

TensorFlow baseline inference has not been approved.

Provider implementation has not been approved.

Production migration has not been approved.

`legacy_musicnn` remains the only production classifier path and baseline.

The default provider remains `legacy_musicnn`.

The production classifier path remains legacy MusiCNN.

The `/classify` contract and response shape remain unchanged:

- `ok`;
- `message`;
- `genres`;
- `genres_pretty`.

Runtime shadow execution remains disabled by default.

`tidal-parser` is unchanged.

## Why Roadmap 4.34 is needed

Roadmap 4.33 planned the future scaffold, but it did not approve
implementation.

PB identity and JSON equivalence are positive artifact evidence, but they are
not numeric parity proof.

Scaffold creation must be separated from inference approval.

Inference execution must be separated from dependency approval.

Provider implementation must be separated from parity evidence.

Production migration must remain behind later approval gates.

## Approval boundaries

Approval to create scaffold code is not approval to run TensorFlow inference.

Approval to create scaffold code is not approval to run ONNX inference.

Approval to create scaffold code is not approval to compare model outputs.

Approval to create scaffold code is not approval to add `onnxruntime` to
production dependencies.

Approval to create scaffold code is not approval to implement a provider.

Approval to create scaffold code is not approval to switch the default
provider.

Approval to create scaffold code is not approval to migrate production.

## Future scaffold location

Recommended future location:

```text
scripts/lightweight/musicnn_onnx_parity_scaffold.py
```

Roadmap 4.34 does not create this file.

## Future scaffold type

The future scaffold, if separately approved, should be:

- local-only;
- CLI-only;
- not imported by the production app;
- not wired into the provider factory;
- not called by `/classify`;
- not used by `tidal-parser`;
- dry-run / metadata-validation first unless separately approved.

## Dependency policy

Production requirements remain unchanged.

`onnxruntime` must not be added to production dependencies.

Roadmap 4.34 includes no dependency changes.

Optional local-only environment notes may be documented later.

A future scaffold must fail gracefully if an optional local runtime is missing.

The initial scaffold should be stdlib-only / dry-run until separate approval.

## Input policy

Only local artifacts from this directory may be used by the future scaffold:

```text
/tmp/music-tools-onnx-parity/
```

Current bundled baseline artifacts may be read from:

```text
app/models/
```

The future scaffold must not add model files to the repository.

The future scaffold must not download models.

The future scaffold must not include network/download logic.

The future scaffold must not add audio fixtures to the repository.

A fixture manifest may be introduced only after separate approval.

Copyrighted audio fixtures are not allowed in the repository.

## Output policy

Roadmap 4.34 creates only this roadmap markdown document.

Future metadata/report artifacts may live under:

```text
docs/lightweight/evaluation/
```

Raw model outputs may be recorded only after separate approval.

Future work must not add:

- large binaries;
- audio files;
- model files.

## Execution policy

Roadmap 4.34 runs no inference.

Roadmap 4.34 runs no TensorFlow inference.

Roadmap 4.34 runs no ONNX inference.

Roadmap 4.34 runs no ONNX Runtime execution.

Roadmap 4.34 makes no `/classify` calls.

A future dry-run / metadata-validation mode may be approved first.

TensorFlow baseline inference requires separate approval.

ONNX inference requires separate approval.

Model output comparison requires separate approval.

## Future evidence family

Future evidence/report artifacts may include, without being created in Roadmap
4.34:

- parity scaffold run report;
- TensorFlow baseline output artifact;
- ONNX output artifact;
- comparison report;
- warnings/no-go items;
- decision status.

## Future comparison dimensions

Future comparison, if separately approved, should cover:

- artifact identity;
- metadata identity;
- preprocessing input compatibility;
- raw output shape;
- `max_abs_diff`;
- `mean_abs_diff`;
- tolerance;
- top-N overlap;
- final genres overlap;
- `genres_pretty` match;
- empty output behavior;
- warning/failure behavior.

## No-go checklist

The future scaffold must be treated as no-go if it:

- imports the production app;
- changes the provider factory;
- calls `/classify`;
- requires model files in the repository;
- adds `onnxruntime` to production requirements;
- modifies Dockerfile;
- modifies Docker Compose;
- changes response shape;
- changes controlled vocabulary;
- claims parity before inference evidence;
- runs inference without approval;
- adds audio fixtures without approval;
- adds network/download logic.

## Decision options

Available decisions:

- approve creation of local-only parity scaffold code in a future step;
- approve only stdlib-only dry-run scaffold first;
- require separate approval for optional local ONNX Runtime environment;
- require separate approval for TensorFlow baseline inference;
- require separate approval for ONNX inference;
- require fixture manifest approval before any audio-based comparison;
- revise scaffold boundaries;
- block until local legal audio fixtures are identified;
- keep `legacy_musicnn` as only production path.

## Recommended decision

Approve only future creation of local-only parity scaffold code in dry-run /
metadata-validation mode.

Do not approve inference yet.

Do not approve `onnxruntime` dependency yet.

Do not approve provider implementation.

Do not approve default provider switch.

Do not approve production migration.

Keep `legacy_musicnn` as the production baseline.

## Explicit non-goals

Roadmap 4.34 explicitly does not include:

- scaffold code;
- parity runner;
- production classifier code;
- provider implementation;
- provider factory changes;
- dependency changes;
- `onnxruntime`;
- model files;
- audio fixtures;
- network/download logic;
- inference;
- TensorFlow/ONNX model execution;
- `/classify` calls;
- controlled vocabulary changes;
- runtime changes;
- Dockerfile changes;
- Docker Compose changes;
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
