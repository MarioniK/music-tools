# Roadmap 4.18 — Small audio tagging candidate research baseline

Status:

- documentation/research safe-slice;
- non-production-facing;
- `not_production_decision: true`;
- no implementation;
- no model integration;
- no runtime changes.

Roadmap 4.18 is not a production decision. It does not select a production
candidate, approve a provider, approve inference, approve a default provider
switch, or approve shadow, canary, or production migration.

## Scope

Roadmap 4.18 is limited to `genre-classifier` and only adds documentation for
a future small audio tagging candidate research lane.

This slice is documentation-only. It does not change production behavior,
runtime behavior, dependencies, Docker files, provider code, provider factory
wiring, cache semantics, `/classify`, or the production response shape.

The current production baseline remains unchanged:

- `legacy_musicnn` remains the default provider;
- the production classifier path remains legacy MusiCNN;
- the `/classify` contract is unchanged;
- the response shape is unchanged:
  - `ok`
  - `message`
  - `genres`
  - `genres_pretty`

`tidal-parser` is out of scope and must remain untouched.

## Current ONNX Lane Status

The ONNX lane is infrastructure-ready but evidence-blocked. Roadmap 4.7 through
Roadmap 4.17 prepared offline evidence shapes, example artifacts, review gates,
and alternatives review language, but they did not approve a real ONNX model or
production migration path.

The ONNX lane is not unblocked. The following remain not approved:

- ONNX smoke inference;
- provider implementation;
- provider factory wiring;
- default provider switch;
- runtime shadow execution;
- canary rollout;
- production migration.

ONNX remains blocked until approved real model provenance, license evidence,
label mapping evidence, output evidence, and baseline-vs-candidate comparison
evidence exist.

## Reason For Opening Small Audio Tagging Lane

Roadmap 4 is looking for a lightweight candidate path after runtime
modernization work. The ONNX lane is currently blocked because there is no real
approved model identity, provenance, license review, label mapping, output, or
comparison evidence.

Small audio tagging may be a useful research lane because it is close to the
existing music genre classification problem and could preserve the existing
offline comparison shape against `legacy_musicnn`. Before any implementation,
the project needs to define what evidence a small audio tagging candidate must
provide.

This step is research discipline, not implementation. It creates a baseline for
future documentation and review only.

## Definition Of Small Audio Tagging Candidate

A small audio tagging candidate is a local lightweight audio tagging or audio
classifier candidate that:

- has clear raw labels;
- may be mapped to the existing controlled genre vocabulary;
- can be evaluated offline against `legacy_musicnn`;
- does not require `/classify` contract changes;
- does not require response shape changes;
- has clear runtime, dependency, model, provenance, and license
  characteristics.

The candidate must be suitable for local-only review and future offline
comparison before any production-facing work can be considered.

## In-Scope Model Families

The following model families are in scope for documentation and research:

- pre-trained lightweight audio tagging models with permissive provenance;
- compact music tagging models with known label vocabularies;
- local-only small classifiers with clear labels;
- audio event or audio tagging models only when music-relevant mapping is
  realistic;
- distillation or teacher-student small tagging models as a future research
  option only.

In-scope status does not approve implementation, dependencies, downloads,
inference, provider work, or production use.

## Out-Of-Scope Model Families

The following are out of scope for Roadmap 4.18:

- full LLM classifier adoption;
- heavy CLAP or embedding stacks as the default lane;
- generic speech or audio event models with no useful music genre mapping
  unless explicitly justified in a future research artifact;
- full TensorFlow replacement implementation;
- provider implementation;
- provider factory wiring;
- models with unclear license or provenance;
- candidates requiring runtime network downloads;
- candidates requiring `/classify` contract changes;
- candidates requiring response shape changes.

## Evaluation Criteria

Future small audio tagging candidates should be evaluated using these criteria:

- model availability;
- license clarity;
- provenance clarity;
- label vocabulary usefulness for music genres;
- controlled vocabulary mapping difficulty;
- runtime weight;
- dependency surface;
- CPU-only feasibility;
- local-only feasibility;
- expected latency;
- model size;
- output interpretability;
- offline evaluation compatibility;
- baseline comparison feasibility;
- rollback simplicity;
- fit with the existing provider boundary;
- fit with the existing artifact/report/evidence workflow;
- production migration risk.

These criteria are for research and review. Passing them in a future document
would still not automatically approve production migration.

## Provenance And License Requirements

A future candidate provenance record must include:

- exact model name;
- stable source reference;
- model version, registry revision, release, tag, commit, or other immutable
  reference;
- license name;
- license evidence link or source reference;
- license compatibility notes;
- redistribution status;
- commercial or non-commercial restrictions;
- weights availability;
- future checksum or hash requirement for the exact reviewed local file;
- label vocabulary source;
- training data notes, when available;
- local-only feasibility;
- confirmation that no runtime download is required.

Candidates with unclear source, license, redistribution, or commercial-use
terms remain blocked.

## Label Mapping Requirements

A future label mapping artifact must include:

- raw label vocabulary;
- raw label examples;
- mapping to the existing controlled genre vocabulary;
- unmapped label policy;
- out-of-vocabulary handling;
- duplicate handling;
- score or confidence handling;
- top-N policy;
- threshold policy;
- major genre shift review;
- mapping review before candidate output is accepted.

The mapping must preserve the existing `/classify` contract and response shape.
If raw labels cannot be mapped to the controlled vocabulary in a useful and
reviewable way, the candidate is no-go.

## Artifact/Report/Evidence Workflow Reuse

Small audio tagging must reuse the existing Roadmap 4 artifact, report, and
evidence discipline developed through Roadmap 4.3 through Roadmap 4.14. Future
work should preserve the same conservative review posture used for ONNX
evidence packages and offline comparisons.

Future evidence artifacts may include:

- provenance artifact;
- label mapping artifact;
- candidate output artifact;
- evaluation report;
- baseline-vs-candidate comparison;
- decision record.

Roadmap 4.18 does not change validators or tests.

## Risk Matrix

| Risk | Mitigation |
| --- | --- |
| Unclear license | Require explicit license evidence, redistribution notes, and commercial-use notes before any offline evaluation approval. |
| Weak music genre vocabulary | Review raw labels before candidate acceptance and reject candidates with no useful controlled-vocabulary mapping. |
| Heavy dependency stack | Treat dependency surface as a primary evaluation criterion and reject candidates that do not fit Roadmap 4 lightweight goals. |
| Poor controlled vocabulary mapping | Require a reviewed label mapping artifact, OOV policy, duplicate handling, and major genre shift review. |
| Quality regression against `legacy_musicnn` | Require offline candidate output and baseline-vs-candidate comparison before any provider discussion. |
| Runtime or network download requirement | Require local-only feasibility and no runtime download requirement; reject candidates that need network access at runtime. |
| Accidental model or audio files in repo | Keep model and audio artifacts prohibited for this slice and verify absence during review. |
| Premature provider implementation | Keep Roadmap 4.18 documentation-only and require a separate approval gate for any provider code. |
| `/classify` contract drift | Require contract and response-shape preservation as no-go criteria. |
| Premature shadow/canary pressure | Record shadow, canary, and production migration as explicitly not approved. |

## No-Go Criteria

A small audio tagging candidate is no-go if any of the following apply:

- unclear license;
- no stable model reference;
- no label vocabulary;
- no usable music mapping;
- runtime network requirement;
- dependency surface too heavy for Roadmap 4 goals;
- inability to compare against `legacy_musicnn`;
- requirement to change `/classify` contract;
- requirement to change response shape.

## Decision Options

Available decision options after this research baseline are:

- continue to small audio tagging provenance/model search;
- continue to small audio tagging spike planning;
- pause small audio tagging and research sklearn/features;
- pause small audio tagging and return to ONNX after real model evidence;
- reject small audio tagging lane for now;
- keep `legacy_musicnn` as only production path.

## Recommended Next Step

The recommended default decision is:

- continue only to documentation/research planning for small audio tagging
  provenance/model search;
- do not start implementation;
- do not add dependencies;
- do not add models;
- keep `legacy_musicnn` as the production baseline;
- keep the ONNX lane infrastructure-ready but evidence-blocked.

This recommendation is not a production candidate selection and does not
approve runtime work.

## Explicit Non-Goals

Roadmap 4.18 does not include:

- production candidate selection;
- production provider implementation;
- provider factory wiring;
- default provider switch;
- shadow execution;
- canary rollout;
- production migration;
- dependency changes;
- Dockerfile changes;
- Docker Compose changes;
- model files;
- model downloads;
- network/download logic;
- copyrighted audio fixtures;
- real inference;
- `/classify` calls;
- runtime changes;
- `tidal-parser` changes;
- response shape changes;
- cache semantics changes;
- LLM cutover;
- tag/release work.

## Allowed Next Steps

Allowed next steps are limited to documentation and research:

- research candidate model families at a documentation level;
- record candidate provenance questions;
- draft future provenance requirements;
- draft future label mapping requirements;
- compare candidate families against the criteria in this document;
- plan a future documentation-only small audio tagging provenance/model search;
- keep `legacy_musicnn` as the production baseline;
- keep ONNX blocked until real approved model evidence exists.

## Prohibited Next Steps

Roadmap 4.18 explicitly prohibits:

- implementation;
- dependencies;
- models;
- inference;
- provider wiring;
- default switch;
- shadow execution;
- canary rollout;
- production migration;
- Docker/runtime changes;
- `tidal-parser` changes.

These prohibitions include provider implementation, provider factory changes,
model downloads, model files, network/download logic, audio artifacts,
copyrighted fixtures, real inference, `/classify` calls, dependency file
changes, Dockerfile changes, Docker Compose changes, cache semantics changes,
response shape changes, LLM cutover, commit, tag, release, or push.

## Rollback Considerations

Rollback is deletion of this single Roadmap 4.18 markdown file:

- `docs/lightweight/roadmap-4.18-small-audio-tagging-candidate-research.md`

Runtime impact is absent. No dependency rollback, provider rollback, Docker
rollback, cache rollback, or contract rollback is required.
