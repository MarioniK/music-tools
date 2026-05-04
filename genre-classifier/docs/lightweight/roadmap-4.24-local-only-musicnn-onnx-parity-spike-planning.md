# Roadmap 4.24 — Local-only MusiCNN ONNX parity spike planning

## Status

Planned documentation safe-slice / planning only.

Roadmap 4.24 is non-production-facing. It prepares a bounded plan for a
future local-only MusiCNN ONNX parity spike and does not approve
implementation, model integration, model download, dependency changes,
provider wiring, shadow execution, canary rollout, production migration, or
release work.

## Scope

This slice is limited to a planning artifact under
`genre-classifier/docs/lightweight/`.

The scope is to:

- prepare a safe plan for a future local-only MusiCNN ONNX parity spike;
- compare the current bundled TensorFlow frozen model path,
  `msd-musicnn-1.pb`, with an official/local `msd-musicnn-1.onnx` in a future
  approved step;
- keep production code, provider default, Docker/runtime behavior, and the
  `/classify` contract unchanged.

No production code, provider implementation, provider factory wiring, default
provider setting, dependency file, Dockerfile, Docker Compose file, model file,
audio fixture, network/download logic, runtime behavior, tests, validators, or
`tidal-parser` file is changed or approved by this document.

## Current production baseline

The current production baseline remains unchanged:

- default provider: `legacy_musicnn`;
- production classifier path: legacy MusiCNN;
- current bundled model artifacts:
  - `msd-musicnn-1.pb`;
  - `msd-musicnn-1.json`;
- current preprocessing/inference path:
  - `ffmpeg`;
  - `MonoLoader`;
  - `TensorflowPredictMusiCNN`;
- response shape unchanged:
  - `ok`;
  - `message`;
  - `genres`;
  - `genres_pretty`;
- `tidal-parser` untouched.

## Why planning is needed after Roadmap 4.23

Roadmap 4.23 produced a strong model identity signal for the current
production `legacy_musicnn` path. The code and bundled metadata strongly
identify the current TensorFlow frozen model path as `msd-musicnn-1.pb` with
matching `msd-musicnn-1.json` metadata.

Roadmap 4.22 found an official Essentia MusiCNN ONNX reference named
`msd-musicnn-1.onnx`. Together, these facts make the official ONNX artifact a
plausible candidate for a future runtime replacement parity review.

However, Roadmap 4.23 did not prove byte-level parity, numeric output parity,
preprocessing equivalence, top-N parity, final `genres` parity, or final
`genres_pretty` parity. Therefore, any future ONNX spike must be local-only,
bounded, evidence-driven, and explicitly separate from production runtime
changes.

## Artifact policy

Future parity work must follow this artifact policy:

- no model files in the repository;
- no official ONNX, PB, or JSON artifacts committed;
- no downloads into the repository;
- no download or network logic in the project;
- use a local temporary path outside the project only, for example:
  `/tmp/music-tools-onnx-parity/`;
- any downloads are manual and require separate approval;
- SHA256, file size, and provenance are recorded in a future report only;
- artifacts must not be staged or committed;
- legal/provenance status must be documented before any wider usage.

The future report may reference absolute local paths for reviewer context, but
the artifacts themselves must remain outside the repository and outside any
commit.

## Future local-only spike inputs

A future approved local-only parity spike may use:

- current bundled `msd-musicnn-1.pb`;
- current bundled `msd-musicnn-1.json`;
- official/local `msd-musicnn-1.onnx`;
- optional official/local `msd-musicnn-1.pb` for hash and identity comparison;
- official/local `msd-musicnn-1.json`;
- one or more local legal audio fixtures, only if already available and
  approved;
- current `TensorflowPredictMusiCNN` path as baseline;
- future isolated ONNX runner script only after separate approval.

These inputs are listed for planning only. Roadmap 4.24 does not download,
create, vendor, stage, execute, or validate any of them.

## Parity comparison dimensions

Future comparison should cover model artifact identity:

- file name;
- file size;
- SHA256;
- metadata model name.

Future comparison should cover metadata parity:

- label vocabulary;
- label order;
- output layer names if available;
- input tensor expectations.

Future comparison should cover preprocessing parity:

- `ffmpeg` / `MonoLoader`;
- sample rate;
- raw audio vs mel, spectrogram, or patch input;
- whether ONNX expects the same input as the TensorFlow predictor.

Future comparison should cover raw output parity:

- output tensor shape;
- max absolute difference;
- mean absolute difference;
- numeric tolerance.

Future comparison should cover semantic parity:

- top-N overlap;
- final `genres` overlap;
- final `genres_pretty` overlap;
- empty output behavior;
- non-genre filtering behavior.

Future comparison should cover resource metrics:

- import time;
- startup time;
- inference latency;
- memory/RSS;
- package footprint;
- Docker image impact only later, not in this stage.

## Metrics

A future report should use explicit metric names:

- `artifact_file_size_bytes`;
- `artifact_sha256`;
- `label_count`;
- `label_vocabulary_match`;
- `label_order_match`;
- `output_shape_match`;
- `max_abs_diff`;
- `mean_abs_diff`;
- `top_n_overlap_ratio`;
- `genres_overlap_ratio`;
- `genres_pretty_match`;
- `empty_output_match`;
- `import_time_ms`;
- `startup_time_ms`;
- `inference_latency_ms`;
- `peak_rss_mb`;
- `dependency_footprint_mb`.

## Success criteria

A future local-only parity spike may continue only if evidence shows:

- same or explainably equivalent model/metadata identity;
- same label vocabulary and label order;
- same preprocessing input or documented safe adaptation;
- raw output similarity within documented tolerance;
- acceptable top-N overlap;
- acceptable final `genres` / `genres_pretty` parity;
- no response shape change required;
- no provider/default switch required;
- no model files in the repository;
- no runtime network requirement;
- rollback remains simple.

## Failure / no-go criteria

The ONNX replacement lane should stop or be revised if evidence shows:

- model identity mismatch;
- label vocabulary mismatch;
- label order mismatch;
- preprocessing input incompatible;
- ONNX output not comparable;
- numeric output drift too large;
- final `genres` drift unacceptable;
- requires response shape change;
- requires provider/default switch to test;
- requires model files in the repository;
- requires runtime network download;
- requires Docker/runtime changes before parity proof;
- requires removing Essentia before proof;
- license/provenance blockers.

## Local-only execution boundaries

Future spike execution boundaries:

- future spike may use local temporary files outside the repository;
- future spike must not mutate production runtime;
- future spike must not call `/classify` unless separately approved;
- future spike must not require Docker image changes before parity proof;
- future spike must not affect the default provider.

## Evidence / report format

A future report should include:

- summary;
- artifact paths, without committing artifacts;
- artifact file sizes;
- SHA256 hashes;
- provenance notes;
- command log;
- fixture list;
- raw output comparison metrics;
- semantic comparison metrics;
- warnings;
- no-go items;
- decision:
  - continue;
  - revise;
  - block;
  - reject.

## Decision options

Possible decisions after reviewing this plan:

- continue to local-only parity spike scaffold;
- continue to model artifact hash/metadata preparation;
- continue to preprocessing parity design;
- block until legal/local audio fixtures are available;
- reject ONNX runtime replacement if planning reveals a hard blocker;
- keep `legacy_musicnn` as the only production path.

## Recommended decision

Recommended Roadmap 4.24 decision:

- do not start implementation in Roadmap 4.24;
- do not add `onnxruntime`;
- do not download model files into the repository;
- do not run inference;
- prepare the plan only;
- if accepted, Roadmap 4.25 may be a local-only parity spike scaffold or local
  artifact preparation step;
- keep `legacy_musicnn` as the production baseline and default provider.

## Explicit non-goals

Roadmap 4.24 does not include:

- no production classifier code changes;
- no provider implementation;
- no provider factory wiring;
- no default-provider switch;
- no `/classify` contract change;
- no response shape change;
- no controlled vocabulary change;
- no runtime/dependency changes;
- no `onnxruntime` dependency;
- no model files;
- no audio fixtures;
- no downloads;
- no download/network logic;
- no inference;
- no `/classify` call;
- no Dockerfile changes;
- no Docker Compose changes;
- no cache semantics changes;
- no `tidal-parser` changes;
- no shadow execution;
- no canary;
- no LLM cutover;
- no production migration;
- no tag/release.

## Allowed next steps

Allowed next steps after Roadmap 4.24:

- review and refine this planning artifact;
- prepare a separate Roadmap 4.25 proposal;
- optionally plan local artifact hash/metadata preparation;
- optionally plan preprocessing parity design.

## Prohibited next steps

Prohibited next steps from Roadmap 4.24:

- adding `onnxruntime` immediately;
- downloading artifacts into the repository;
- committing model files;
- wiring a provider;
- changing the default provider;
- changing the Docker image;
- running production inference;
- changing the `/classify` response.

## Rollback considerations

Rollback is deletion of this single markdown document.

No runtime rollback is required because Roadmap 4.24 allows no runtime code,
dependency, Docker, model, audio fixture, provider wiring, inference, or API
contract changes.

Any temporary report generated during this slice must be removed before commit
and must not be staged or committed.
