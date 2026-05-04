# Roadmap 4.27 - Local-only MusiCNN ONNX artifact metadata evidence report preparation

## Status

Documentation and sample-only structure preparation.

Roadmap 4.27 prepares the shape of a future local-only MusiCNN ONNX artifact
metadata evidence report. It follows Roadmap 4.25's placeholder template and
Roadmap 4.26's validator coverage by documenting how a later real evidence
report should be reviewed before any local-only artifact preparation or parity
scaffold work.

This is not a parity spike, inference approval, production approval, model
integration, runtime change, dependency change, or provider change.

## Purpose

Roadmap 4.25 added a template for future local-only MusiCNN ONNX artifact
metadata. Roadmap 4.26 added validator coverage for that template. Roadmap 4.27
adds the next safety gate: an evidence report preparation document and
sample-only report shape that explain how real local artifact evidence should
be captured later.

This intermediate gate is needed because future local-only artifact work should
not move directly from a template to parity scaffold. A reviewer should first be
able to inspect provenance, license notes, local paths, measured file sizes,
measured SHA256 hashes, repository exclusion checks, and no-go items without
running inference or changing production behavior.

This is still not a parity spike because it does not prepare real artifacts,
download models, compare outputs, run `/classify`, add providers, add
`onnxruntime`, or execute any candidate MusiCNN ONNX inference path.

## Baseline

The production baseline remains unchanged:

- default provider: `legacy_musicnn`;
- production classifier path: legacy MusiCNN;
- current bundled artifacts:
  - `msd-musicnn-1.pb`;
  - `msd-musicnn-1.json`;
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

Any future real evidence report or parity scaffold must treat `legacy_musicnn`
as the baseline unless a separate production decision changes it.

## Distinction

### Template

The existing local MusiCNN ONNX artifact metadata template is structure only.

It contains no real official/local artifacts, keeps measured fields such as
`file_size_bytes`, `sha256`, and real `local_path` values as `null`, and is
always not approved for inference or production.

### Sample evidence report

A sample evidence report is an example-only shape for reviewers and future
automation.

It contains no real artifacts, no real local paths, no fake measured values, no
inference approval, and no production approval. It may keep measured fields as
`null` and must explicitly identify itself as sample-only.

### Real evidence report

A real evidence report may be created only after separate approval.

It contains measured values from prepared local artifacts, remains local-only,
and still does not approve production. It is an input to future review before a
parity scaffold is considered.

## Future Real Evidence Report Fields

Future real evidence reports should include these top-level or per-artifact
fields, as appropriate:

- `schema_version`;
- `report_type`;
- `report_id`;
- `candidate_family`;
- `purpose`;
- `not_production_decision`;
- `approved_for_inference`;
- `approved_for_production`;
- `generated_at`;
- `generated_by`;
- `local_environment`;
- `artifacts`;
- `artifact_role`;
- `artifact_name`;
- `source_url`;
- `source_reference_type`;
- `local_path`;
- `local_only`;
- `artifact_downloaded`;
- `artifact_in_repo`;
- `committed_to_repo`;
- `file_size_bytes`;
- `sha256`;
- `provenance_notes`;
- `license_notes`;
- `verification_commands`;
- `verification_results`;
- `warnings`;
- `no_go_items`;
- `review_status`;
- `next_step_recommendation`.

## Evidence Report Rules

Template and sample reports may keep measured fields as `null`.

A real evidence report must:

- include measured `file_size_bytes` and `sha256` values for prepared local
  artifacts;
- verify prepared artifacts are outside the repository;
- verify prepared artifacts are not staged or committed;
- avoid fake hashes and fake file sizes;
- avoid approving inference automatically;
- avoid approving production automatically;
- be reviewed before any parity scaffold.

## Review Gate Before Local-only Parity Scaffold

Before any local-only parity scaffold is prepared, review must confirm:

- no model files are in the repository;
- no downloaded artifacts are in the repository;
- no fake hashes are present;
- no fake file sizes are present;
- local-only paths are documented only after approval;
- provenance notes are reviewed;
- license notes are reviewed;
- inference approval remains `false` until separate approval;
- production approval remains `false`;
- `legacy_musicnn` remains the baseline.

## Decision Options

Future review may choose one of these decisions:

- continue to local-only artifact evidence report validator coverage;
- continue to local-only parity scaffold preparation;
- block until manual local artifacts are approved;
- revise evidence report structure;
- keep `legacy_musicnn` as the only production path.

## Recommended Default Decision

For this safe-slice, the recommended default decision is:

- do not download artifacts;
- do not add model files;
- do not add `onnxruntime`;
- do not run inference;
- prepare evidence report structure/sample only;
- keep `legacy_musicnn` as production baseline and default provider.

## Explicit Non-goals

Roadmap 4.27 does not include:

- production classifier code changes;
- provider implementation;
- provider factory changes;
- default-provider switch;
- `onnxruntime` or dependency changes;
- model downloads;
- model files;
- audio fixtures;
- network/download logic;
- inference;
- `/classify` calls;
- controlled vocabulary changes;
- runtime changes;
- Dockerfile changes;
- Docker Compose changes;
- cache semantics changes;
- `tidal-parser` changes;
- shadow execution;
- canary rollout;
- LLM cutover;
- production migration;
- tag or release work.

## Sample JSON Artifact Decision

Roadmap 4.27 may include
`docs/lightweight/evaluation/model-provenance/example-local-musicnn-onnx-artifact-metadata-evidence-report.json`
as sample-only documentation.

The current lightweight evaluation validator enumerates specific JSON files
rather than validating every JSON file under `model-provenance`, so this sample
can be added without changing validator code or tests. If a future validator
starts validating sample evidence reports, it should preserve the distinction
between sample-only reports and real measured reports.

The sample report must remain example-only:

- no real local paths;
- `local_path: null`;
- `sha256: null`;
- `file_size_bytes: null`;
- `approved_for_inference: false`;
- `approved_for_production: false`;
- `not_production_decision: true`;
- `artifact_downloaded: false`;
- `artifact_in_repo: false`;
- `committed_to_repo: false`;
- review status not approved;
- no fake hash-looking values;
- no fake file sizes;
- no real measured values;
- explicit sample-only semantics.

## Validation Expectations

Review checks for this safe-slice should confirm:

- sample JSON, if present, is valid JSON;
- the diff is limited to documentation/sample metadata and the temporary
  report;
- no inference was run;
- `/classify` was not called;
- no model files were downloaded;
- no model files were added;
- no audio fixtures were added;
- no dependency changes were made;
- no Dockerfile or Docker Compose changes were made;
- no provider, default provider, or runtime changes were made;
- `tidal-parser` was not touched;
- no commit, tag, or push was made.
