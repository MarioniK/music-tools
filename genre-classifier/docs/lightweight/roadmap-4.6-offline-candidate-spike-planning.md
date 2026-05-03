# Roadmap 4.6 — Offline candidate spike planning and acceptance criteria

## Status

- documentation/design safe-slice
- non-production-facing
- no production behavior change

## Scope

This document selects the first candidate family for a future offline spike and records the acceptance criteria that must be reviewed before that spike begins.

Roadmap 4.6 does not add a model, runtime, provider, inference path, dependency, or production integration. It does not change the production classifier behavior, the default provider, the `/classify` contract, or the response shape.

## Decision context

Roadmap 4.4 added a minimal loader and validator for lightweight evaluation artifacts. That created a basic way to inspect structured offline evidence before treating it as useful decision input.

Roadmap 4.5 added the report validator, required report sections, warning categories, and a tiny static comparison helper. That made the evaluation artifact shape more reviewable and gave future candidate reports a consistent validation target.

Roadmap 4.6 adds the planning and acceptance layer before the first real offline candidate spike. The goal is to choose the first candidate family, define the evidence that must be collected, and keep approval gates explicit before any runtime, provider, or inference work is allowed.

## Selected first candidate family

Selected first candidate family for a future offline spike:

- ONNX Runtime audio classifier path

This is only a first candidate family selection for future offline evaluation. It is not a production decision, not a provider switch, and not a runtime dependency addition in Roadmap 4.6.

## Why ONNX Runtime first

ONNX Runtime is selected first because it is a plausible lightweight classifier lane that can be evaluated locally and compared in isolation against the current baseline.

Rationale:

- potentially lighter than the TensorFlow / `essentia-tensorflow` production path
- local inference friendly
- easier to package and compare as an isolated candidate
- suitable for offline parity evaluation against `legacy_musicnn`
- does not require LLM or prompt semantics
- can fit a future provider boundary without changing the `/classify` contract

Risks that must be reviewed before adoption assumptions:

- model quality is unknown
- preprocessing may be non-trivial
- vocabulary mismatch is possible
- license or provenance may block adoption
- runtime footprint must still be measured
- no production assumptions are allowed before evaluation

## Backup / secondary candidate family

Backup or secondary candidate family:

- small audio tagging model

This remains a backup lane and is not implemented in parallel during Roadmap 4.6. It may be considered if the ONNX candidate fails quality, licensing, provenance, preprocessing, or resource criteria.

## Baseline

`legacy_musicnn` remains the baseline for all candidate evaluation.

Current baseline constraints:

- default provider remains `legacy_musicnn`
- production classifier path remains legacy MusiCNN
- all candidates must be evaluated against current `legacy_musicnn` outputs
- `/classify` contract and response shape remain unchanged:
  - `ok`
  - `message`
  - `genres`
  - `genres_pretty`

## Spike prerequisites

Before Roadmap 4.7 begins, these prerequisites must be satisfied:

- Roadmap 4.6 document reviewed and approved
- candidate model shortlist identified
- license and provenance reviewed before adding artifacts
- minimal fixture set defined
- evaluation report template remains compatible with Roadmap 4.5 validator expectations
- no production switch allowed
- resource measurement method agreed
- no dependency added before explicit spike approval

## Minimal fixture set

Roadmap 4.6 does not add audio fixtures. The future offline spike must define fixture coverage conceptually before adding or using any files.

Minimal fixture coverage should include:

- diverse genres
- obvious mainstream cases
- ambiguous or cross-genre cases
- electronic, rock, pop, hip-hop, jazz, ambient, or similar broad coverage
- low-confidence or edge cases
- expected empty or failure handling cases where applicable
- fixture metadata sufficient for comparison

Fixture metadata must be sufficient to identify the sample, source/provenance, intended coverage category, licensing status, and comparison notes.

## Quality / parity criteria

Candidate outputs must be represented in a `/classify`-compatible shape for evaluation:

- `ok`
- `message`
- `genres`
- `genres_pretty`

Acceptance criteria for quality and parity:

- candidate genres must map into the controlled vocabulary
- OOV terms must be tracked and treated as warnings or failures depending on severity
- top-N overlap against the `legacy_musicnn` baseline must be measured
- major genre shifts must be flagged
- empty outputs must be flagged
- candidate failures must be explicit
- candidate output does not need perfect equality with `legacy_musicnn`, but differences must be explainable and stable

No real metrics are claimed by this document. All quality, parity, and drift evidence must be collected during a future approved offline spike.

## Resource targets

The future offline spike must measure resource impact rather than assume improvement.

Target categories to measure:

- import/startup overhead
- memory footprint
- per-file inference latency
- model size
- container/runtime weight
- CPU-only viability

Provisional acceptance criteria:

- candidate resource use must be measured under a documented method
- CPU-only execution should be viable for baseline spike success
- optional GPU acceleration may be recorded, but must not be required for baseline spike success
- runtime weight must be compared against the current TensorFlow / `essentia-tensorflow` path before any adoption decision

## Licensing and model provenance checks

No model artifact may be added until license and provenance are acceptable.

Required checks:

- model license
- redistribution rights
- commercial or non-commercial restrictions
- source repository or model card
- training data notes where available
- version and hash tracking
- compatibility with repository publication
- no model artifact added until license/provenance is acceptable

## Allowed changes for future Roadmap 4.7

Only after explicit approval, Roadmap 4.7 may allow:

- offline-only candidate spike document/update
- optional isolated experimental script under `scripts/lightweight`, if explicitly approved
- optional static candidate output examples
- optional dependency proposal document
- optional model shortlist metadata document

Roadmap 4.7 does not allow production provider implementation by default. Any production-facing implementation must be separately approved.

## Prohibited changes

Roadmap 4.6 prohibits:

- no production classifier code changes
- no provider implementation
- no default provider switch
- no `/classify` contract change
- no response shape change
- no cache semantics changes
- no Dockerfile / Docker Compose changes
- no runtime dependency changes
- no model/audio artifacts
- no actual inference
- no shadow execution
- no canary
- no `tidal-parser` changes
- no LLM cutover
- no release/tag work

## Approval gates

Required gates:

- document review gate
- candidate/license/provenance gate
- fixture coverage gate
- dependency/runtime impact gate
- offline spike approval gate
- later provider integration gate
- separate production switch gate

Passing one gate does not imply passing later gates. In particular, approving the offline spike does not approve provider integration or production switching.

## No-go criteria

The candidate lane must stop or be reconsidered if any of these conditions apply:

- license/provenance unclear or incompatible
- candidate requires a heavy runtime comparable to or worse than the current TensorFlow path
- candidate cannot produce `/classify`-compatible output
- high OOV rate
- frequent empty outputs
- unacceptable top-N overlap or severe genre drift
- preprocessing too brittle
- candidate requires GPU as a hard requirement
- candidate would require response contract redesign
- candidate would force `tidal-parser` changes

## Rollback considerations

Roadmap 4.6 rollback is documentation-only.

Rollback action:

- remove or revert this one markdown file

No runtime rebuild is needed. No cache migration is needed. No dependency cleanup is needed. Any future Roadmap 4.7 spike must remain separately reversible.

## Non-goals

- no production migration
- no model integration
- no provider implementation
- no inference
- no default switch
- no shadow/canary
- no release work
