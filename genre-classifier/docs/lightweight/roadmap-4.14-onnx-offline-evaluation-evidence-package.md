# Roadmap 4.14 - ONNX Offline Evaluation Evidence Package

Status: offline-only evidence packaging / decision record safe slice.

## Purpose

Roadmap 4.14 defines a single evidence package format for ONNX offline
evaluation review. It follows Roadmap 4.13, which can generate a markdown report
from existing static baseline and candidate output artifacts, by making the
review bundle explicit and machine-checkable.

The evidence package is a decision record for offline review only. It is not a
production decision, not a provider implementation, not a default-provider
switch, and not approval to run ONNX in production.

## Why This Package Exists

Roadmap 4.13 produces a report, but a report alone can drift away from the
inputs that made it. The Roadmap 4.14 package ties the report back to the
specific artifacts used for the review:

- model provenance artifact;
- label mapping artifact;
- evaluation manifest;
- legacy baseline output;
- ONNX candidate output;
- generated markdown report;
- validator and test command results;
- decision status, approval gates, no-go checklist, warnings, and known gaps.

Keeping those references together makes later review reproducible enough to
answer the important offline question: what evidence was reviewed, what was
missing, and why was the decision status chosen?

## Production Invariant

`legacy_musicnn` remains the baseline because it is the current production
classifier path and the default provider. The `/classify` contract is unchanged,
and the production response shape remains:

- `ok`
- `message`
- `genres`
- `genres_pretty`

An ONNX candidate may only be compared offline in this slice. The evidence
package must not imply that the candidate is connected to the provider factory,
allowed to shadow production traffic, approved for canary use, or selected as a
new default provider.

## Required Evidence Inputs

A complete package references these inputs:

- `model_provenance_path`: ONNX model identity, source, license, hash, expected
  input/output metadata, label source, approval status, warnings, and known
  limitations.
- `label_mapping_path`: raw label to controlled-vocabulary mapping decisions,
  unmapped labels, mapping approval status, and mapping warnings.
- `manifest_path`: offline fixture manifest used for the comparison.
- `baseline_output_path`: output from `legacy_musicnn`, preserving the
  production-compatible response fields.
- `candidate_output_path`: offline ONNX candidate output, preserving the same
  response shape for comparison and adding evaluation-only metadata outside the
  production contract.
- `report_path`: generated markdown report that summarizes aggregate comparison,
  controlled vocabulary results, OOV results, top-N overlap, resource metrics,
  warnings, known gaps, and decision.
- `validation`: validator and test commands with recorded results.

## Required Package Fields

The sample package at
`docs/lightweight/evaluation/evidence/example-onnx-evidence-package.json`
demonstrates the required top-level fields:

- `schema_version`
- `package_id`
- `package_type`
- `created_at`
- `decision_status`
- `decision_summary`
- `not_production_decision`
- `baseline_provider`
- `candidate_provider`
- `candidate_family`
- `artifacts`
- `model_provenance_path`
- `label_mapping_path`
- `manifest_path`
- `baseline_output_path`
- `candidate_output_path`
- `report_path`
- `validation`
- `validator_command`
- `validator_result`
- `tests_command`
- `tests_result`
- `approvals`
- `approval_gates`
- `no_go_checklist`
- `warnings`
- `known_gaps`
- `next_step_recommendation`

`package_type` must be
`onnx_offline_evaluation_evidence_package`.
`not_production_decision` must be `true`.

## Decision Statuses

Allowed `decision_status` values:

- `continue`: offline evidence is sufficient to continue to the next offline
  review step, without approving production use.
- `revise`: evidence exists, but the package needs correction or additional
  offline data before continuing.
- `reject`: evidence supports stopping this candidate path.
- `blocked`: required evidence or approvals are missing, so no next migration
  step is allowed.

The example package uses `blocked` because it is example-only and deliberately
contains placeholder provenance, unapproved mapping, unclear license data, and
no real runtime evaluation.

## Approval Gates

Approval gates keep review state visible. A package should include gates for:

- model provenance approval;
- label mapping approval;
- manifest and fixture review;
- generated report review;
- validator success;
- lightweight test success;
- unresolved major genre shift review;
- OOV rate review;
- runtime metric review;
- model license review;
- explicit confirmation that production provider work is not requested by this
  package.

Passing gates in this package can only support an offline next step. A separate
roadmap item would be required for provider implementation, runtime wiring,
shadow execution, canary rollout, or default-provider change.

## No-Go Checklist

The package should carry no-go items explicitly so missing evidence cannot be
mistaken for approval. Expected categories include:

- `provenance_not_approved`
- `label_mapping_not_approved`
- `model_hash_mismatch`
- `label_count_mismatch`
- `candidate_output_missing`
- `generated_report_missing`
- `validator_failed`
- `tests_failed`
- `major_genre_shift_unresolved`
- `oov_rate_unknown_or_too_high`
- `runtime_metrics_missing`
- `model_license_unclear`
- `production_dependency_required`
- `provider_switch_requested_prematurely`
- `shadow_canary_requested_prematurely`

Any active no-go item should force `decision_status` to `blocked`, `revise`, or
`reject`, not `continue`.

## Warnings And Known Gaps

Warnings are review facts, not log noise. They should capture uncertainty such
as incomplete provenance, unapproved mapping, missing runtime metrics, OOV
terms, major genre shifts, fixture gaps, incomplete comparison data, unclear
license terms, or accidental requests for production behavior.

Known gaps should name the evidence still missing before any future production
planning can begin. The package format keeps warnings and known gaps as lists so
reviewers can scan them and validators can check their container shape without
loading models or executing inference.

## Validation Approach

`scripts/lightweight/validate_evaluation_artifacts.py` performs shallow static
validation only. For evidence packages it checks:

- JSON readability;
- required fields;
- expected `package_type`;
- allowed `decision_status`;
- `not_production_decision == true`;
- artifact path fields are strings;
- validation command/result fields exist;
- `approval_gates`, `no_go_checklist`, `warnings`, and `known_gaps` are lists.

The validator remains stdlib-only. It does not import production provider or
runtime modules, does not import ONNX Runtime, does not load model files, does
not run inference, and does not call `/classify`.

Targeted lightweight tests cover the valid sample and failure cases for missing
required fields, invalid decision status, and `not_production_decision: false`.

## Explicit Non-Goals

Roadmap 4.14 does not:

- change production classifier code;
- add a production provider implementation;
- connect an ONNX candidate to the provider factory;
- change the default provider from `legacy_musicnn`;
- change the production classifier path;
- change the `/classify` contract;
- change the response shape;
- change runtime behavior;
- change dependencies;
- change Dockerfile or Docker Compose;
- add `onnxruntime`;
- add TFLite, sklearn, model, or audio dependencies;
- add model files;
- add audio files;
- download anything;
- add network or download logic;
- run real inference;
- call `/classify`;
- touch `tidal-parser`;
- create shadow or canary logic;
- start production migration.

## Rollback Considerations

Rollback is documentation and static-artifact cleanup only. Remove:

- this Roadmap 4.14 document;
- `docs/lightweight/evaluation/evidence/example-onnx-evidence-package.json`;
- the evidence-package branch of the lightweight validator;
- the targeted evidence-package tests.

No production runtime, provider factory, default provider, `/classify`
contract, response shape, dependencies, Docker configuration, model files, audio
files, or `tidal-parser` code are changed by this slice.
