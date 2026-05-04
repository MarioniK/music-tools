# Roadmap 4.25 — Local-only MusiCNN ONNX artifact metadata preparation

## Status

Planned safe-slice / documentation and sample metadata template only.

Roadmap 4.25 prepares documentation and a placeholder-only metadata template
for a future local-only MusiCNN ONNX artifact metadata report. It does not
approve production implementation, model integration, model download,
inference, `/classify` calls, dependency changes, provider wiring, shadow
execution, canary rollout, production migration, or release work.

## Scope

This slice is limited to documentation and sample metadata under
`genre-classifier/docs/lightweight/`.

The scope is to:

- define the expected metadata report shape for future local-only official
  MusiCNN ONNX artifacts;
- document which artifact identity, provenance, hash, size, and approval fields
  must be captured later;
- provide a placeholder-only JSON template that is not evidence;
- preserve the current production classifier behavior and `/classify` contract.

No production classifier code, `app/` code, provider factory, provider
implementation, default provider setting, dependency file, Dockerfile, Docker
Compose file, model file, audio fixture, network/download logic, controlled
vocabulary, tests, scripts, or `tidal-parser` file is changed or approved by
this document.

## Current production baseline

The current production baseline remains unchanged:

- default provider: `legacy_musicnn`;
- production classifier path: legacy MusiCNN;
- current baseline artifacts:
  - bundled `msd-musicnn-1.pb`;
  - bundled `msd-musicnn-1.json`;
- current preprocessing/inference path:
  - `ffmpeg`;
  - `MonoLoader`;
  - `TensorflowPredictMusiCNN`;
- `/classify` contract unchanged;
- response shape unchanged:
  - `ok`;
  - `message`;
  - `genres`;
  - `genres_pretty`;
- `tidal-parser` untouched.

Any future parity spike must compare against this current `legacy_musicnn`
baseline.

## Why metadata preparation is needed after Roadmap 4.24

Roadmap 4.24 prepared a planning gate for a future local-only MusiCNN ONNX
parity spike. That planning gate identified the need to compare the current
bundled TensorFlow frozen model path against official/local MusiCNN ONNX
artifacts before any runtime work can be considered.

Roadmap 4.25 adds the next safe documentation slice: a metadata report design
that can later capture artifact identity and provenance without downloading
models, committing artifacts, running inference, changing providers, or
touching production behavior.

This step is needed because future ONNX parity work must not rely on informal
artifact assumptions. File names, local paths, source URLs, SHA256 hashes, file
sizes, license notes, and approval flags must be recorded explicitly. Missing
values must remain `null` or clearly marked as example-only. No fake SHA256
hashes or fake file sizes are allowed.

## Artifact metadata report design

A future artifact metadata report should be a local-only evidence document. It
may describe current bundled artifacts and future manually prepared official
local artifacts, but it must not contain model bytes or imply production
approval.

Recommended top-level fields:

- `schema_version`;
- `report_type`;
- `report_id`;
- `candidate_family`;
- `purpose`;
- `not_production_decision`;
- `approved_for_inference`;
- `approved_for_production`;
- `created_at`;
- `generated_by`;
- `artifacts`;
- `validation_status`;
- `warnings`;
- `no_go_items`;
- `next_step_recommendation`.

Recommended per-artifact fields:

- `artifact_role`;
- `artifact_name`;
- `source_url`;
- `local_path`;
- `local_only`;
- `artifact_downloaded`;
- `artifact_in_repo`;
- `committed_to_repo`;
- `file_size_bytes`;
- `sha256`;
- `provenance_notes`;
- `license_notes`.

## Required fields

Future reports should include artifact entries for these roles:

- `current_bundled_pb`;
- `current_bundled_json`;
- `official_local_onnx`;
- `optional_official_local_pb`;
- `official_local_json`.

For real evidence, each downloaded or inspected artifact must have:

- verified local path outside the repository;
- exact file size in bytes;
- exact SHA256 hash;
- source URL or source-origin notes;
- provenance notes;
- license notes;
- explicit confirmation that the artifact is not committed to the repository.

Until those values are measured from real local files, they must remain `null`.

## Template semantics

The JSON template is placeholder-only. It is not an evidence report.

The template:

- does not prove artifact identity;
- does not prove provenance;
- does not prove license acceptability;
- does not approve inference;
- does not approve production;
- does not approve provider changes;
- does not approve dependency changes;
- does not approve a default-provider switch;
- does not approve `/classify` calls;
- must keep real hashes as `null`;
- must keep real file sizes as `null`;
- must keep real local paths as `null` or clearly example-only.

The template may be copied into a future temporary report outside the repository
only after separate approval. The template itself is documentation, not
evidence.

## Local-only artifact policy

Future official/local artifacts must be local-only and outside the repository.

Recommended local-only path:

`/tmp/music-tools-onnx-parity/`

Rules:

- real model artifacts must not be committed;
- official ONNX, PB, or JSON artifacts must not be downloaded into the
  repository;
- no `*.onnx`, `*.pb`, `*.h5`, `*.wav`, `*.mp3`, or `*.flac` artifacts may be
  added by this slice;
- no network/download logic may be added;
- no fake SHA256 hashes may be written;
- no fake file sizes may be written;
- artifacts must not be staged or committed;
- artifact reports must not imply production approval.

## Future manual preparation flow

A future approved manual flow may:

1. Create `/tmp/music-tools-onnx-parity/`.
2. Manually place official/local MusiCNN ONNX metadata inputs there, outside
   the repository.
3. Record source URLs or source-origin notes.
4. Measure exact SHA256 hashes from local files.
5. Measure exact file sizes in bytes from local files.
6. Compare local official metadata with current bundled `msd-musicnn-1.json`.
7. Write a temporary metadata report outside the repository or in a separately
   approved documentation location.
8. Review no-go items before any inference or parity spike is considered.

This flow is future-only. Roadmap 4.25 does not perform it.

## Commit safety rules

Allowed in this slice:

- markdown documentation under `docs/lightweight/`;
- placeholder-only JSON template under
  `docs/lightweight/evaluation/model-provenance/`.

Not allowed in this slice:

- real model artifacts;
- real audio fixtures;
- downloaded official artifacts;
- fake hashes;
- fake file sizes;
- production code changes;
- dependency changes;
- Docker changes;
- provider/default changes;
- `app/`, `tests/`, or `scripts/` changes;
- `tidal-parser` changes;
- staging, commits, tags, or pushes.

## Validation expectations

Review checks for this safe-slice should confirm:

- the JSON template is valid JSON;
- the diff is limited to documentation/sample metadata under
  `docs/lightweight/`;
- no model or audio artifacts were added;
- no downloads were performed;
- no inference was run;
- `/classify` was not called;
- dependency, runtime, Docker, provider, and production code paths were not
  changed;
- `tidal-parser` was not touched.

## No-go checklist

Future work must stop or remain documentation-only if any item is true:

- official/local artifact source is unknown;
- artifact is inside the repository;
- artifact was committed or staged;
- SHA256 hash is missing for real evidence;
- file size is missing for real evidence;
- hash or file size is guessed;
- license status is unknown and required for the intended next step;
- label metadata does not match the current baseline;
- preprocessing compatibility is unknown;
- inference would require provider or dependency changes before evidence review;
- production behavior would change before parity proof;
- `/classify` contract would change;
- response shape would change.

## Decision options

Future metadata review may choose one of these decisions:

- `continue_to_local_only_parity_spike`: metadata is complete enough for a
  separately approved local-only parity spike;
- `revise_metadata`: metadata is incomplete but recoverable;
- `block_on_provenance`: source, license, hash, or file-size evidence is not
  acceptable;
- `reject_candidate`: artifact identity or policy mismatch makes the candidate
  unsuitable.

## Recommended decision

The recommended Roadmap 4.25 decision is:

`revise_metadata_until_real_local_evidence_exists`

This means the placeholder template may exist in the repository, but no future
ONNX inference, production implementation, provider wiring, dependency change,
or default-provider switch should proceed until a real local-only metadata
report exists and is reviewed against the current `legacy_musicnn` baseline.

## Explicit non-goals

Roadmap 4.25 does not:

- implement ONNX inference;
- integrate a model;
- download a model;
- add `onnxruntime`;
- add providers;
- change the provider factory;
- switch the default provider;
- change `legacy_musicnn`;
- change `/classify`;
- change the response shape;
- change the controlled vocabulary;
- run shadow execution;
- run a canary;
- prepare production migration;
- add Docker or Docker Compose changes;
- add model files;
- add audio fixtures;
- touch `tidal-parser`.

## Allowed next steps

Allowed next steps after this slice:

- review the markdown documentation;
- validate the JSON template syntax;
- refine metadata field names while keeping the template placeholder-only;
- prepare a separately approved local-only evidence collection plan;
- compare any future evidence against the current `legacy_musicnn` baseline.

## Prohibited next steps

Prohibited next steps without separate approval:

- downloading official ONNX, PB, or JSON artifacts into the repository;
- committing real model or metadata artifacts from official sources;
- adding inference code;
- adding download code;
- adding dependencies;
- changing Docker or Docker Compose files;
- changing provider factory or provider defaults;
- calling `/classify`;
- running inference;
- staging or committing a temporary report;
- touching `tidal-parser`;
- migrating production traffic.

## Rollback considerations

Rollback is documentation-only:

- remove this markdown document;
- remove the placeholder JSON template if present;
- leave production code, runtime dependencies, provider defaults, Docker files,
  model artifacts, audio fixtures, and `tidal-parser` unchanged.

Because this slice has no runtime behavior, rollback should not affect
`/classify`, the default `legacy_musicnn` provider, or the current bundled
`msd-musicnn-1.pb` / `msd-musicnn-1.json` production baseline.
