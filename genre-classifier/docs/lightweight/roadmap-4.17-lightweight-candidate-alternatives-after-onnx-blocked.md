# Roadmap 4.17 — Lightweight candidate alternatives review after ONNX blocked gate

Status:

- documentation/design safe-slice;
- alternatives review only;
- `not_production_decision: true`;
- no provider implementation approved;
- no default provider switch approved;
- no shadow/canary/migration approved.

## Scope

Roadmap 4.17 reviews lightweight classifier candidate alternatives after the
ONNX lane reached an evidence-blocked gate. This stage is a documentation-only
design review intended to compare possible future research lanes without
changing production behavior.

This slice does not implement a provider, run inference, download a model, add
model files, add dependencies, change runtime wiring, or change Docker and
Docker Compose files. It does not alter validators, tests, cache semantics, the
provider factory, `/classify`, or `tidal-parser`.

## Current Production Baseline

The current production baseline remains unchanged:

- `legacy_musicnn` remains the default provider;
- the production classifier path remains legacy MusiCNN;
- the `/classify` contract is unchanged;
- the response shape is unchanged:
  - `ok`
  - `message`
  - `genres`
  - `genres_pretty`

## Current ONNX Lane Status

The ONNX lane is infrastructure-ready but evidence-blocked. Roadmap 4.7 through
Roadmap 4.16 prepared scaffolding, example artifacts, evidence package shape,
decision gate language, and provenance flow for a future real local ONNX
candidate.

Those artifacts do not select a production candidate and do not approve ONNX
execution. The ONNX lane remains blocked until approved real model evidence,
mapping evidence, output evidence, and comparison evidence exist.

## Why ONNX Remains Blocked

ONNX remains blocked because the repository still lacks the evidence required
to evaluate a concrete candidate safely:

- approved real local ONNX model provenance;
- approved label mapping for a concrete model;
- reviewed license/source evidence;
- SHA256 hash for the exact reviewed local model file;
- input/output tensor metadata;
- real candidate output;
- baseline-vs-candidate comparison against `legacy_musicnn`;
- runtime metrics;
- major genre shift review;
- OOV rate review.

Without that evidence, any ONNX result would be difficult to reproduce, license
review would remain incomplete, and model output could not be safely compared
against the existing controlled vocabulary or production baseline.

## Why Provider Implementation Is Not Approved

Provider code without real model evidence would create speculative production
surface. It would add runtime concepts before reviewers know which model,
license, tensor contract, label mapping, or output behavior the provider is
supposed to support.

No dependency, runtime, provider, or factory wiring should be added during this
stage. Provider implementation requires a separate approval gate after real
candidate evidence has been reviewed.

## Alternatives Review Criteria

Future lightweight candidate lanes should be compared using these criteria:

- runtime weight reduction potential;
- dependency risk;
- model availability;
- license/provenance clarity;
- label mapping complexity;
- controlled vocabulary compatibility;
- expected genre quality;
- offline evaluation feasibility;
- implementation complexity;
- rollback simplicity;
- production migration risk;
- fit with the existing provider boundary;
- fit with the existing artifact/report/evidence workflow.

## Candidate Alternatives Matrix

| Candidate family | Potential upside | Main risks | Evidence required before implementation | Suitability as next research lane |
| --- | --- | --- | --- | --- |
| ONNX Runtime | Could reduce runtime weight if a small, suitable audio tagging model exists; previous roadmap slices already prepared evidence and report scaffolding. | Still blocked by missing real model identity, license review, tensor metadata, hash, mapping, and output comparison; runtime dependency may still be non-trivial. | Approved real local ONNX provenance, license/source evidence, SHA256, tensor metadata, label mapping, candidate output, baseline comparison, runtime metrics, OOV and major genre shift review. | Not suitable to continue until real approved model evidence exists. Keep blocked. |
| TFLite | May offer small runtime footprint and mobile/edge-oriented model formats. | Model availability for genre/audio tagging may be limited; conversion provenance can be unclear; label mapping and preprocessing may be model-specific; new runtime dependency would need review. | Concrete TFLite model source, license, file hash, tensor metadata, preprocessing contract, label mapping, output evidence, baseline comparison, runtime metrics. | Possible later research lane, but not preferred until a strong candidate model is identified. |
| sklearn / lightweight ML over audio features | Potentially very small dependency/runtime footprint if built on already available feature extraction; simple rollback and explainable features. | Genre quality may be significantly weaker than learned audio taggers; training data and feature consistency can become new evidence burdens; may need additional feature dependencies. | Feature set definition, training/evaluation provenance, label mapping, controlled vocabulary fit, baseline comparison, runtime metrics, quality review, license/data review. | Useful backup research lane, especially for dependency minimization, but quality risk may be higher. |
| CLAP / audio embeddings + classifier | Strong semantic audio embeddings could support flexible classification and better generalization. | Embedding models may be large; runtime and dependency weight may be high; license/model provenance and label mapping still require review. | Concrete embedding model provenance, license, hash, embedding metadata, classifier design, label mapping, output evidence, baseline comparison, runtime metrics. | Promising for research, but dependency/runtime weight risk makes it less conservative as the immediate next lane. |
| Small audio tagging models | Closest to the current genre/audio tagging problem; may provide lighter inference than the TensorFlow/MusiCNN stack while preserving a comparable offline evaluation shape. | Model labels may not match the controlled genre vocabulary; provenance and license quality varies; preprocessing assumptions may differ from production. | Model identity, source/license review, hash, tensor/input metadata, label list, label mapping, candidate output, baseline comparison, runtime metrics, OOV and genre shift review. | Best next documentation/research lane because it aligns with the existing problem and evidence workflow. |
| Rule-assisted audio feature classifier | Very small runtime surface and transparent decisions; may be simple to roll back. | Quality and genre coverage are likely limited; rules may encode brittle assumptions; difficult to match MusiCNN behavior on ambiguous tracks. | Feature definitions, rule rationale, fixture coverage, controlled vocabulary mapping, baseline comparison, OOV and major genre shift review. | Useful as a fallback or diagnostic lane, not as the primary lightweight candidate. |
| Teacher/student lightweight model trained against legacy outputs | Could preserve legacy behavior while reducing runtime weight; direct comparison target is clear because `legacy_musicnn` acts as teacher. | Requires training pipeline, data governance, model provenance, evaluation design, and possible model artifact management; may reproduce legacy errors. | Training data policy, teacher output artifacts, student model provenance, license/data review, hash, label mapping, baseline comparison, runtime metrics, drift review. | Potentially strong later lane, but too large for the next conservative documentation slice. |
| Optional remote/local lightweight provider as research-only lane | Could compare local and remote lightweight behavior conceptually without changing production defaults. | Remote behavior introduces network, privacy, availability, reproducibility, and contract risks; local/remote duality complicates provider boundaries. | Research-only threat model, data handling review, provenance, response mapping, offline comparison substitute, rollback and privacy review. | Not suitable for near-term implementation; only acceptable as a tightly scoped research note. |

## Decision Options

Available decision options after this alternatives review are:

- continue ONNX only after real approved model evidence exists;
- pause ONNX and research a small audio tagging lane;
- pause ONNX and research a sklearn/features lane;
- pause ONNX and research a CLAP/embeddings lane;
- reject non-TensorFlow alternatives for now;
- keep `legacy_musicnn` as the only production path.

## Recommended Decision

The recommended decision is:

- pause the ONNX lane as infrastructure-ready but evidence-blocked;
- do not unblock the ONNX lane;
- do not approve ONNX smoke inference;
- do not approve provider implementation;
- do not approve a default provider switch;
- do not approve shadow/canary/production migration;
- open Roadmap 4.18 as a documentation/research safe-slice for the small
  audio tagging candidate lane;
- keep `legacy_musicnn` as the production baseline.

This is not a production candidate selection. It is a conservative research
direction for the next documentation-only stage.

## Recommended Next Research Lane

The recommended next research lane is a small audio tagging candidate lane,
limited to documentation and research. This lane is closest to the current
genre/audio tagging problem, may be lighter than the TensorFlow/MusiCNN stack,
and should be easier to evaluate with the existing offline artifact/report
workflow than broader architecture changes.

A small audio tagging candidate can be compared against the `legacy_musicnn`
baseline using the same evidence discipline already developed in Roadmap 4.7
through Roadmap 4.16. It still requires provenance, license, hash, tensor
metadata, label mapping, candidate output, runtime metrics, and baseline
comparison evidence before any implementation can be considered.

The sklearn/features lane remains a backup research option, but quality risk
may be higher. The CLAP/embeddings lane is promising, but may carry dependency
and runtime weight risk. No production candidate is selected by Roadmap 4.17.

## Explicit Non-Goals

Roadmap 4.17 does not include:

- production provider implementation;
- provider factory wiring;
- default provider switch;
- shadow execution;
- canary rollout;
- production migration;
- runtime changes;
- dependency changes;
- Dockerfile / Docker Compose changes;
- model files;
- model downloads;
- network/download logic;
- copyrighted audio fixtures;
- real inference;
- `/classify` calls;
- `/classify` contract changes;
- response shape changes;
- `tidal-parser` changes;
- LLM cutover;
- tag/release work.

## Allowed Next Steps

Allowed next steps are limited to documentation and research planning:

- draft Roadmap 4.18 documentation/research safe-slice for a small audio
  tagging candidate lane;
- define evidence requirements for the small audio tagging candidate lane;
- define provenance/license/mapping checklist for that lane;
- compare expected risks against ONNX and sklearn/features;
- keep ONNX blocked until real approved evidence exists.

## Prohibited Next Steps

The following next steps are prohibited by this decision:

- adding dependencies;
- adding model files;
- downloading models;
- adding network/download logic;
- adding provider code;
- wiring provider factory;
- changing the default provider;
- running inference;
- calling `/classify`;
- changing runtime, Docker, or dependencies;
- touching `tidal-parser`;
- creating a tag or release.

## Rollback Considerations

Rollback is deletion or edit of this one documentation artifact. No runtime
rollback is required. No dependency rollback is required. No provider rollback
is required. No cache or contract rollback is required.
