# Roadmap 4.16 - Real ONNX Candidate Provenance Preparation

Status: documentation/sample artifact safe-slice.

## Scope

Roadmap 4.16 prepares the documentation shape for a future real local ONNX
model provenance artifact after the Roadmap 4.15 decision gate remained
blocked.

This slice is evidence preparation only. It is non-production-facing and does
not approve real inference, smoke inference, model download, model files in the
repository, provider implementation, provider factory changes, a default
provider switch, shadow or canary execution, or production migration.

The production baseline remains `legacy_musicnn`. The production classifier
path remains unchanged. The `/classify` contract and response shape remain:

- `ok`
- `message`
- `genres`
- `genres_pretty`

`tidal-parser` is untouched.

## Current Decision

The ONNX lane remains blocked after Roadmap 4.16 unless a future step provides
real model metadata and closes the open gates. Roadmap 4.16 is not approval to
run an ONNX model and is not a production decision.

Roadmap 4.15 left the lane blocked because the repository still lacks:

- approved real local ONNX model provenance;
- approved label mapping for that exact model;
- reviewed model license evidence;
- real candidate output;
- real baseline-vs-candidate comparison;
- runtime metrics;
- OOV and major genre shift review.

Roadmap 4.16 addresses only the first part of that gap: how a future real
candidate provenance record should be prepared and reviewed. It does not fill
that record with invented data.

## Why Preparation Is Needed

The Roadmap 4.15 gate is blocked because the existing evidence is example-only.
A future real ONNX candidate needs a precise, reviewable identity before any
offline evaluation can be meaningful. Reviewers must be able to answer which
file was inspected, where it came from, which license applies, which labels it
emits, and whether its input/output contract can be compared against
`legacy_musicnn` without changing production behavior.

Provenance preparation also prevents process drift. If smoke inference starts
before source, license, hash, labels, and tensor metadata are reviewed, the
result can look technical while remaining unreproducible or legally unclear.

## Why Smoke Inference Is Not Approved

Smoke inference is not approved yet because there is no approved real local
model record. Running inference before provenance review would skip the gates
that Roadmap 4.9 and Roadmap 4.15 deliberately placed before experimentation:

- source and license are not reviewed;
- exact file identity and SHA-256 are missing;
- label source and label mapping are not approved;
- input/output metadata is not reviewed;
- candidate output, runtime metrics, OOV review, and major genre shift review
  would have no trusted provenance anchor.

Any future smoke run requires a separate approval after real metadata exists.

## Prohibited In This Slice

Roadmap 4.16 does not:

- run real inference;
- call `/classify`;
- download models;
- add model files;
- add audio artifacts;
- add download scripts;
- add network logic;
- add `onnxruntime` or other runtime/model dependencies;
- change runtime or dependency files;
- change Dockerfile or Docker Compose;
- implement an ONNX provider;
- change provider implementation;
- change provider factory wiring;
- change the default provider;
- change production classifier code paths;
- change `/classify`;
- change the response shape;
- create shadow or canary logic;
- start production migration;
- touch `tidal-parser`.

Model files and download logic are prohibited because this slice is a review
artifact preparation step, not an acquisition or execution step. Adding a model
binary could accidentally redistribute a file with unclear rights, increase
repository size, and blur the boundary between documentation and runtime state.
Adding download logic would introduce network behavior before the source and
license review has approved that source.

## Fake Provenance Is Prohibited

Fake source URLs, fake hashes, fake licenses, fake model names, and invented
approval rationales are prohibited. Placeholder provenance cannot identify a
real model, cannot prove file integrity, cannot establish license safety, and
cannot support reproducible comparison.

The default state for any real candidate template is therefore
`not_approved`. Without real model metadata, the only truthful artifact is a
template or incomplete record that explicitly says it is not approved for
offline evaluation.

## Required Future Provenance Fields

A future real local ONNX provenance artifact must record:

- `candidate_id`: stable identifier for the reviewed candidate.
- `model_name`: model name from the authoritative source.
- `model_version`: release, revision, tag, registry revision, or commit.
- `model_format`: expected to be `onnx`.
- `local_filename`: file name used locally.
- `local_path_policy`: local-only path policy; the file is not committed.
- `sha256`: SHA-256 for the exact local file.
- `file_size_bytes`: size of the exact local file in bytes.
- `source_origin`: publisher, project, or model registry identity.
- `source_url`: authoritative source URL for provenance, not a download
  instruction.
- `manual_local_only_retrieval_method`: human-reviewed local retrieval steps.
- `license_name`: explicit license name.
- `license_url`: license file or model-card URL.
- `license_review_status`: review state for license and redistribution.
- `redistribution_notes`: whether the file may be committed, packaged, or
  redistributed, if known.
- `commercial_use_notes`: commercial-use constraints, if known.
- `input_tensor_metadata`: names, shapes, dtypes, sample rate assumptions,
  mono/stereo handling, duration/windowing, and preprocessing notes.
- `output_tensor_metadata`: names, shapes, dtypes, output meaning, and
  postprocessing notes.
- `label_source`: authoritative label source.
- `label_count`: exact output label count.
- `label_mapping_artifact`: path or link to the future label mapping artifact.
- `baseline_provider`: must be `legacy_musicnn`.
- `approval_status`: current review status.
- `approved_for_offline_evaluation`: boolean approval marker.
- `not_production_decision`: must be `true`.
- `no_go_items`: active blockers and prohibited conditions.

Missing real values keep the candidate `not_approved` or `blocked`.

## Local SHA-256 Strategy

For Linux:

```bash
sha256sum /absolute/local/path/to/model.onnx
```

For macOS:

```bash
shasum -a 256 /absolute/local/path/to/model.onnx
```

The recorded hash must be for the exact file reviewed. A changed file, changed
source revision, changed file size, or hash mismatch creates a new candidate
review. A placeholder hash is invalid for inference.

## Source, License, And Version Strategy

The future record must cite an authoritative source and a stable model version.
Acceptable version anchors include a release, tag, commit SHA, model registry
revision, or immutable artifact version. The record must separate source
identity from file identity: a source URL tells reviewers where the model came
from, while SHA-256 and file size identify the local file.

License review must name the license, link to the license evidence, and record
review status. If redistribution or commercial-use rights are unclear, the
candidate remains blocked. Source URLs in the artifact are provenance evidence;
they are not download instructions and must not trigger network behavior.

## Input And Output Metadata Strategy

Input metadata must be specific enough to determine whether a local offline
experiment can prepare audio tensors without changing production code. It
should include tensor names, shapes, dtypes, sample rate, channel handling,
windowing, preprocessing transforms, and any normalization requirements.

Output metadata must state tensor names, shapes, dtypes, score meaning, output
ordering, and postprocessing. The output must be compatible with a future
offline candidate artifact that preserves the production-compatible fields
`genres` and `genres_pretty`.

## Future Label Mapping Linkage

The provenance artifact must link to a separate future label mapping artifact
for the exact model and exact label order. That artifact must document label
source, label count, raw indexes, controlled-vocabulary mapping decisions,
unmapped labels, warnings, and approval status.

If label count, label order, or label source is missing or inconsistent, the
candidate remains blocked. If labels cannot be mapped to the existing
controlled genre vocabulary without changing `/classify`, the candidate is
no-go.

## Approval Status Model

Future real candidate records should use these statuses:

- `not_approved`: default for templates or incomplete real metadata.
- `ready_for_review`: real metadata is present and awaiting review.
- `approved_for_offline_evaluation`: source, license, local file identity,
  tensor metadata, and label linkage are reviewed for offline evaluation only.
- `rejected`: candidate failed review.
- `blocked`: required evidence is missing or a no-go item is active.

Moving from `not_approved` to `approved_for_offline_evaluation` requires:

- real model identity and version from an authoritative source;
- explicit license name and license evidence;
- reviewed redistribution and commercial-use notes when relevant;
- local-only handling with no committed model file;
- exact local file name, file size, and SHA-256;
- input and output tensor metadata sufficient for offline evaluation;
- label source, label count, and future label mapping artifact path;
- baseline provider fixed as `legacy_musicnn`;
- active no-go items cleared or explicitly reviewed as non-blocking;
- explicit statement that this is not a production decision.

`approved_for_offline_evaluation` still does not approve provider
implementation, provider factory wiring, default-provider changes, shadow or
canary traffic, production migration, dependency changes, Docker changes,
committed model files, downloads, or `/classify` contract changes.

## Open No-Go Items

Until real data exists, the following no-go items remain active:

- `real_model_identity_missing`
- `real_source_missing`
- `real_model_version_missing`
- `real_sha256_missing`
- `real_file_size_missing`
- `license_review_missing`
- `redistribution_review_missing`
- `input_tensor_metadata_missing`
- `output_tensor_metadata_missing`
- `label_source_missing`
- `label_mapping_not_approved`
- `candidate_output_missing`
- `baseline_vs_candidate_report_missing`
- `runtime_metrics_missing`
- `oov_review_missing`
- `major_genre_shift_review_missing`
- `smoke_inference_not_approved`

These items keep the ONNX lane blocked after Roadmap 4.16.

## Template Artifact

The optional template artifact is:

- `docs/lightweight/evaluation/model-provenance/template-real-onnx-model-provenance.json`

It is a placeholder template only. It intentionally contains no fake hash, no
fake source, no fake license, no fake model identity, and no approval rationale
pretending that real review happened. Its default approval status is
`not_approved`, `approved_for_offline_evaluation` is `false`, and
`not_production_decision` is `true`.

## Rollback Considerations

Rollback for Roadmap 4.16 is documentation/template cleanup only. Remove:

- this Roadmap 4.16 document;
- `docs/lightweight/evaluation/model-provenance/template-real-onnx-model-provenance.json`.

No production classifier code, provider factory, default provider, runtime
dependencies, Docker configuration, model files, audio artifacts, `/classify`
contract, response shape, shadow execution, canary configuration, or
`tidal-parser` files are changed by this slice.
